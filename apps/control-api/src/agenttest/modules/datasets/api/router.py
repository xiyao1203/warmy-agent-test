"""HTTP routes for project-scoped Dataset assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from agenttest.bootstrap.settings import Settings
from agenttest.modules.datasets.api.schemas import (
    CreateDatasetRequest,
    CreateTestCaseRequest,
    DatasetListResponse,
    DatasetResponse,
    DatasetVersionListResponse,
    DatasetVersionResponse,
    ExportTestCasesResponse,
    ImportTestCasesRequest,
    ImportTestCasesResponse,
    TestCaseListResponse,
    TestCaseResponse,
    UpdateDatasetRequest,
    UpdateTestCaseRequest,
)
from agenttest.modules.datasets.application.commands import (
    AddTestCaseCommand,
    CreateDatasetCommand,
    CreateDatasetVersionCommand,
    DatasetNotFoundError,
    DatasetVersionNotEditableError,
    DatasetVersionNotFoundError,
    DeleteTestCaseCommand,
    PublishDatasetVersionCommand,
    TestCaseNotFoundError,
    UpdateDatasetCommand,
    UpdateTestCaseCommand,
)
from agenttest.modules.datasets.application.import_export import (
    ImportError as DatasetImportError,
)
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"
ExportFormat = Literal["json", "jsonl", "csv"]


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class ListDatasetsExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Dataset], str | None]: ...


class GetDatasetExecutor(Protocol):
    async def execute(self, actor: User, dataset_id: DatasetId) -> Dataset: ...


class CreateDatasetExecutor(Protocol):
    async def execute(self, actor: User, command: CreateDatasetCommand) -> Dataset: ...


class UpdateDatasetExecutor(Protocol):
    async def execute(self, actor: User, command: UpdateDatasetCommand) -> Dataset: ...


class ListVersionsExecutor(Protocol):
    async def execute(self, actor: User, dataset_id: DatasetId) -> list[DatasetVersion]: ...


class GetVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        version_id: DatasetVersionId,
    ) -> DatasetVersion: ...


class CreateVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: CreateDatasetVersionCommand,
    ) -> DatasetVersion: ...


class PublishVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: PublishDatasetVersionCommand,
    ) -> DatasetVersion: ...


class ListCasesExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[TestCase], str | None]: ...


class GetCaseExecutor(Protocol):
    async def execute(self, actor: User, case_id: TestCaseId) -> TestCase: ...


class AddCaseExecutor(Protocol):
    async def execute(self, actor: User, command: AddTestCaseCommand) -> TestCase: ...


class UpdateCaseExecutor(Protocol):
    async def execute(self, actor: User, command: UpdateTestCaseCommand) -> TestCase: ...


class DeleteCaseExecutor(Protocol):
    async def execute(self, actor: User, command: DeleteTestCaseCommand) -> None: ...


class ImportExportExecutor(Protocol):
    async def import_test_cases(
        self,
        *,
        actor: User,
        dataset: Dataset,
        version: DatasetVersion,
        format: str,
        content: str,
    ) -> list[TestCase]: ...

    async def export_test_cases(
        self,
        *,
        version: DatasetVersion,
        format: ExportFormat,
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class DatasetApiDependencies:
    list_datasets: ListDatasetsExecutor
    get_dataset: GetDatasetExecutor
    create_dataset: CreateDatasetExecutor
    update_dataset: UpdateDatasetExecutor
    list_versions: ListVersionsExecutor
    get_version: GetVersionExecutor
    create_version: CreateVersionExecutor
    list_cases: ListCasesExecutor
    get_case: GetCaseExecutor
    add_case: AddCaseExecutor
    update_case: UpdateCaseExecutor
    delete_case: DeleteCaseExecutor
    publish_version: PublishVersionExecutor
    import_export: ImportExportExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_dataset_router(
    dependencies: DatasetApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["datasets"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return authentication_required()
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return authentication_required()

    async def writer(request: Request, csrf_header: str | None) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or not cookie or csrf_header != cookie:
            return csrf_failed()
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return csrf_failed()
        return actor

    async def project_dataset(
        actor: User,
        project_id: UUID,
        dataset_id: UUID,
    ) -> Dataset:
        dataset = await dependencies.get_dataset.execute(actor, DatasetId(dataset_id))
        if dataset.project_id != ProjectId(project_id):
            raise DatasetNotFoundError(DatasetId(dataset_id))
        return dataset

    async def project_version(
        actor: User,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
    ) -> tuple[Dataset, DatasetVersion]:
        dataset = await project_dataset(actor, project_id, dataset_id)
        version = await dependencies.get_version.execute(
            actor,
            DatasetVersionId(version_id),
        )
        if version.dataset_id != dataset.dataset_id:
            raise DatasetVersionNotFoundError(DatasetVersionId(version_id))
        return dataset, version

    async def project_case(
        actor: User,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        case_id: UUID,
    ) -> TestCase:
        _, version = await project_version(actor, project_id, dataset_id, version_id)
        case = await dependencies.get_case.execute(actor, TestCaseId(case_id))
        if case.dataset_version_id != version.version_id:
            raise TestCaseNotFoundError(TestCaseId(case_id))
        return case

    @router.get("", response_model=DatasetListResponse)
    async def list_datasets(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = None,
    ) -> DatasetListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, next_cursor = await dependencies.list_datasets.execute(
                actor,
                ProjectId(project_id),
                limit=limit,
                cursor=cursor,
            )
        except ProjectNotFoundError:
            return asset_not_found()
        return DatasetListResponse(
            items=[DatasetResponse.from_domain(item) for item in items],
            next_cursor=next_cursor,
        )

    @router.post("", response_model=DatasetResponse, status_code=201)
    async def create_dataset(
        request: Request,
        project_id: UUID,
        payload: CreateDatasetRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> DatasetResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                dataset = await dependencies.create_dataset.execute(
                    actor,
                    CreateDatasetCommand(
                        project_id=ProjectId(project_id),
                        name=payload.name,
                        description=payload.description,
                    ),
                )
        except ProjectNotFoundError:
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return DatasetResponse.from_domain(dataset)

    @router.get("/{dataset_id}", response_model=DatasetResponse)
    async def get_dataset(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
    ) -> DatasetResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            dataset = await project_dataset(actor, project_id, dataset_id)
        except (DatasetNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        return DatasetResponse.from_domain(dataset)

    @router.patch("/{dataset_id}", response_model=DatasetResponse)
    async def update_dataset(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        payload: UpdateDatasetRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> DatasetResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_dataset(actor, project_id, dataset_id)
            async with dependencies.uow_factory():
                dataset = await dependencies.update_dataset.execute(
                    actor,
                    UpdateDatasetCommand(
                        dataset_id=DatasetId(dataset_id),
                        name=payload.name,
                        description=payload.description,
                    ),
                )
        except (DatasetNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return DatasetResponse.from_domain(dataset)

    @router.get("/{dataset_id}/versions", response_model=DatasetVersionListResponse)
    async def list_versions(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
    ) -> DatasetVersionListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_dataset(actor, project_id, dataset_id)
            versions = await dependencies.list_versions.execute(
                actor,
                DatasetId(dataset_id),
            )
        except (DatasetNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        return DatasetVersionListResponse(
            items=[DatasetVersionResponse.from_domain(item) for item in versions]
        )

    @router.post(
        "/{dataset_id}/versions",
        response_model=DatasetVersionResponse,
        status_code=201,
    )
    async def create_version(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> DatasetVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_dataset(actor, project_id, dataset_id)
            async with dependencies.uow_factory():
                version = await dependencies.create_version.execute(
                    actor,
                    CreateDatasetVersionCommand(dataset_id=DatasetId(dataset_id)),
                )
        except (DatasetNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        return DatasetVersionResponse.from_domain(version)

    @router.get(
        "/{dataset_id}/versions/{version_id}",
        response_model=DatasetVersionResponse,
    )
    async def get_version(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
    ) -> DatasetVersionResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            _, version = await project_version(actor, project_id, dataset_id, version_id)
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        return DatasetVersionResponse.from_domain(version)

    @router.post(
        "/{dataset_id}/versions/{version_id}/publish",
        response_model=DatasetVersionResponse,
    )
    async def publish_version(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> DatasetVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, dataset_id, version_id)
            async with dependencies.uow_factory():
                version = await dependencies.publish_version.execute(
                    actor,
                    PublishDatasetVersionCommand(
                        version_id=DatasetVersionId(version_id)
                    ),
                )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return conflict(str(error))
        return DatasetVersionResponse.from_domain(version)

    @router.get(
        "/{dataset_id}/versions/{version_id}/cases",
        response_model=TestCaseListResponse,
    )
    async def list_cases(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        limit: int = Query(default=200, ge=1, le=500),
        cursor: str | None = None,
    ) -> TestCaseListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, dataset_id, version_id)
            items, next_cursor = await dependencies.list_cases.execute(
                actor,
                DatasetVersionId(version_id),
                limit=limit,
                cursor=cursor,
            )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        return TestCaseListResponse(
            items=[TestCaseResponse.from_domain(item) for item in items],
            next_cursor=next_cursor,
        )

    @router.post(
        "/{dataset_id}/versions/{version_id}/cases",
        response_model=TestCaseResponse,
        status_code=201,
    )
    async def add_case(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        payload: CreateTestCaseRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestCaseResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, dataset_id, version_id)
            async with dependencies.uow_factory():
                case = await dependencies.add_case.execute(
                    actor,
                    AddTestCaseCommand(
                        dataset_version_id=DatasetVersionId(version_id),
                        **payload.model_dump(),
                    ),
                )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except DatasetVersionNotEditableError as error:
            return conflict(str(error))
        except ValueError as error:
            return invalid_request(str(error))
        return TestCaseResponse.from_domain(case)

    @router.patch(
        "/{dataset_id}/versions/{version_id}/cases/{case_id}",
        response_model=TestCaseResponse,
    )
    async def update_case(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        case_id: UUID,
        payload: UpdateTestCaseRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestCaseResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_case(actor, project_id, dataset_id, version_id, case_id)
            async with dependencies.uow_factory():
                case = await dependencies.update_case.execute(
                    actor,
                    UpdateTestCaseCommand(
                        case_id=TestCaseId(case_id),
                        **payload.model_dump(),
                    ),
                )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            TestCaseNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except DatasetVersionNotEditableError as error:
            return conflict(str(error))
        except ValueError as error:
            return invalid_request(str(error))
        return TestCaseResponse.from_domain(case)

    @router.delete(
        "/{dataset_id}/versions/{version_id}/cases/{case_id}",
        status_code=204,
        response_model=None,
    )
    async def delete_case(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        case_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_case(actor, project_id, dataset_id, version_id, case_id)
            async with dependencies.uow_factory():
                await dependencies.delete_case.execute(
                    actor,
                    DeleteTestCaseCommand(case_id=TestCaseId(case_id)),
                )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            TestCaseNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except DatasetVersionNotEditableError as error:
            return conflict(str(error))
        return Response(status_code=204)

    @router.post(
        "/{dataset_id}/versions/{version_id}/import",
        response_model=ImportTestCasesResponse,
        status_code=201,
    )
    async def import_cases(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        payload: ImportTestCasesRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> ImportTestCasesResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            dataset, version = await project_version(
                actor,
                project_id,
                dataset_id,
                version_id,
            )
            async with dependencies.uow_factory():
                cases = await dependencies.import_export.import_test_cases(
                    actor=actor,
                    dataset=dataset,
                    version=version,
                    format=payload.format,
                    content=payload.content,
                )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except DatasetImportError as error:
            return import_failed(error.errors)
        except ValueError as error:
            return invalid_request(str(error))
        return ImportTestCasesResponse(
            imported_count=len(cases),
            items=[TestCaseResponse.from_domain(item) for item in cases],
        )

    @router.get(
        "/{dataset_id}/versions/{version_id}/export",
        response_model=ExportTestCasesResponse,
    )
    async def export_cases(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        format: Annotated[ExportFormat, Query()] = "json",
    ) -> ExportTestCasesResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            _, version = await project_version(actor, project_id, dataset_id, version_id)
            content = await dependencies.import_export.export_test_cases(
                version=version,
                format=format,
            )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        return ExportTestCasesResponse(format=format, content=content)

    # ── 批量删除用例 ──────────────────────────────────────────────────────

    @router.post(
        "{dataset_id}/versions/{version_id}/cases/batch-delete",
        response_model=dict,
    )
    async def batch_delete_cases(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> dict | JSONResponse:
        """批量删除用例（从 request body 读取 case_ids）。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, dataset_id, version_id)
            body = await request.json()
            case_ids_raw = body.get("case_ids", [])
            case_ids = [UUID(str(c)) for c in case_ids_raw]
            if not case_ids:
                return invalid_request("case_ids is required")
            async with dependencies.uow_factory():
                for cid in case_ids:
                    await dependencies.delete_case.execute(
                        actor,
                        DeleteTestCaseCommand(
                            case_id=TestCaseId(cid),
                            version_id=DatasetVersionId(version_id),
                        ),
                    )
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            TestCaseNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except (PermissionError, ValueError):
            return permission_denied()
        return {"deleted": len(case_ids)}

    # ── 从失败运行生成用例 ─────────────────────────────────────────────────

    @router.post(
        "{dataset_id}/versions/{version_id}/generate-from-run",
        response_model=dict,
    )
    async def generate_from_run_endpoint(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> dict | JSONResponse:
        """从失败运行生成测试用例。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, dataset_id, version_id)
        except (
            DatasetNotFoundError,
            DatasetVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        try:
            body = await request.json()
            run_id = body.get("run_id")
            if not run_id:
                return invalid_request("run_id is required")
        except Exception:
            return invalid_request("Invalid request body")

        from agenttest.modules.datasets.application.generate_from_run import (
            GenerateFromRunCommand,
            generate_cases_from_failed_run,
        )
        from agenttest.modules.projects.public import ProjectId as Pid

        result = await generate_cases_from_failed_run(
            actor=actor,
            project_id=Pid(project_id),
            command=GenerateFromRunCommand(
                run_id=UUID(str(run_id)),
                dataset_version_id=version_id,
            ),
        )
        return {
            "status": "completed",
            "generated": len(result.generated_cases),
            "total_failed": result.total_failed,
            "message": f"已从失败运行提取 {len(result.generated_cases)} 条用例",
        }

    return router


def authentication_required() -> JSONResponse:
    return problem_response(401, "Authentication required", "A valid session is required")


def csrf_failed() -> JSONResponse:
    return problem_response(403, "CSRF validation failed", "A valid CSRF token is required")


def permission_denied() -> JSONResponse:
    return problem_response(403, "Permission denied", "Project editor access is required")


def asset_not_found() -> JSONResponse:
    return problem_response(404, "Asset not found", "Asset was not found")


def invalid_request(detail: str) -> JSONResponse:
    return problem_response(400, "Invalid request", detail)


def conflict(detail: str) -> JSONResponse:
    return problem_response(409, "Conflict", detail)


def import_failed(errors: list[dict[str, object]]) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "title": "Import failed",
            "status": 400,
            "detail": "One or more rows are invalid",
            "errors": errors,
        },
        media_type="application/problem+json",
    )


def problem_response(status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
