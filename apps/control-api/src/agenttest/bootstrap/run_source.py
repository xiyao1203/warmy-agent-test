from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.domain.invocation import invocation_from_stored_config
from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure.models import BrowserProfileModel
from agenttest.modules.datasets.application.trial_runs import (
    CaseTrialRuntime,
    CaseTrialRuntimeSource,
)
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.datasets.infrastructure.persistence.repositories import (
    _to_test_case,
)
from agenttest.modules.datasets.public import build_case_spec_snapshot
from agenttest.modules.environments.infrastructure.persistence.models import (
    CredentialBindingModel,
    EnvironmentTemplateModel,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import RunDefinition, RunDefinitionCase
from agenttest.modules.scorers.infrastructure.persistence.models import (
    ScorerModel,
    ScorerVersionModel,
)
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.modules.test_plans.public import TestPlanVersionId
from agenttest.shared.infrastructure.database import session_scope


def secret_free_credential_bindings(
    bindings: list[dict[str, object]],
) -> list[dict[str, object]]:
    allowed = ("id", "kind", "injection_location", "injection_name")
    return [{key: item[key] for key in allowed if key in item} for item in bindings]


def browser_profile_snapshot(profile: BrowserProfile) -> dict[str, object]:
    if (
        profile.auth_state_status != "ready"
        or not profile.auth_state_sha256
        or profile.auth_state_version <= 0
    ):
        raise ValueError("Browser profile auth state is not ready")
    return {
        "browser_profile_id": str(profile.id),
        "auth_state_version": profile.auth_state_version,
        "auth_state_sha256": profile.auth_state_sha256,
    }


class SqlAlchemyRunSource:
    """在组合根读取已发布资产并构造不可变运行快照。

    该适配器位于 bootstrap 层，避免 `runs` 业务模块直接依赖其他模块
    的持久化细节；`runs` 模块只看到 `RunSourcePort`。
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def load(
        self,
        project_id: ProjectId,
        version_id: TestPlanVersionId,
    ) -> RunDefinition:
        statement = (
            select(
                TestPlanVersionModel,
                AgentVersionModel,
                AgentModel,
                DatasetVersionModel,
                EnvironmentTemplateModel,
            )
            .join(
                TestPlanModel,
                TestPlanModel.id == TestPlanVersionModel.test_plan_id,
            )
            .join(
                AgentVersionModel,
                AgentVersionModel.id == TestPlanVersionModel.agent_version_id,
            )
            .join(AgentModel, AgentModel.id == AgentVersionModel.agent_id)
            .join(
                DatasetVersionModel,
                DatasetVersionModel.id == TestPlanVersionModel.dataset_version_id,
            )
            .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
            .outerjoin(
                EnvironmentTemplateModel,
                EnvironmentTemplateModel.id == TestPlanVersionModel.environment_template_id,
            )
            .where(
                TestPlanVersionModel.id == version_id.value,
                TestPlanModel.project_id == project_id.value,
                AgentModel.project_id == project_id.value,
                DatasetModel.project_id == project_id.value,
                or_(
                    TestPlanVersionModel.environment_template_id.is_(None),
                    EnvironmentTemplateModel.project_id == project_id.value,
                ),
                TestPlanVersionModel.status == "published",
                AgentVersionModel.status == "published",
                DatasetVersionModel.status == "published",
            )
        )
        async with session_scope(self._session_factory) as session:
            row = (await session.execute(statement)).one_or_none()
            if row is None:
                raise ValueError("Published test plan version was not found")
            plan_version, agent_version, agent, dataset_version, environment = row
            stored_agent_config = dict(agent_version.config)
            target_config = stored_agent_config.get("target_config")
            target_config = dict(target_config) if isinstance(target_config, dict) else {}
            login_config = target_config.get("login")
            login_config = dict(login_config) if isinstance(login_config, dict) else {}
            profile_snapshot: dict[str, object] | None = None
            if str(login_config.get("strategy") or "") == "browser_profile":
                raw_profile_id = target_config.get("browser_profile_id")
                if not raw_profile_id:
                    raise ValueError("Published Agent browser profile is missing")
                try:
                    profile_id = UUID(str(raw_profile_id))
                except ValueError as error:
                    raise ValueError("Published Agent browser profile id is invalid") from error
                profile = await session.scalar(
                    select(BrowserProfileModel).where(
                        BrowserProfileModel.id == profile_id,
                        BrowserProfileModel.project_id == project_id.value,
                        BrowserProfileModel.auth_state_status == "ready",
                    )
                )
                if (
                    profile is None
                    or not profile.auth_state_sha256
                    or profile.auth_state_version <= 0
                ):
                    raise ValueError("Published Agent browser profile auth state is not ready")
                profile_snapshot = {
                    "browser_profile_id": str(profile.id),
                    "auth_state_version": profile.auth_state_version,
                    "auth_state_sha256": profile.auth_state_sha256,
                }
            environment_config = dict(environment.config) if environment else {}
            credential_ids_raw = environment_config.get("credential_binding_ids", [])
            credential_ids = (
                [UUID(str(item)) for item in credential_ids_raw]
                if isinstance(credential_ids_raw, list)
                else []
            )
            credentials = []
            if credential_ids:
                credential_rows = list(
                    (
                        await session.scalars(
                            select(CredentialBindingModel).where(
                                CredentialBindingModel.project_id == project_id.value,
                                CredentialBindingModel.id.in_(credential_ids),
                            )
                        )
                    ).all()
                )
                if len(credential_rows) != len(set(credential_ids)):
                    raise ValueError("Environment references a missing project credential")
                credentials = secret_free_credential_bindings(
                    [
                        {
                            "id": str(item.id),
                            "kind": item.kind,
                            "injection_location": item.injection_location,
                            "injection_name": item.injection_name,
                        }
                        for item in credential_rows
                    ]
                )
            environment_config["credential_bindings"] = credentials
            # ── 加载已发布评分器版本配置 ────────────────────────────
            scorer_ids_raw = plan_version.config.get("scorer_ids", [])
            scorer_configs: list[dict[str, object]] = []
            if isinstance(scorer_ids_raw, list) and scorer_ids_raw:
                scorer_rows = list(
                    (
                        await session.scalars(
                            select(ScorerVersionModel, ScorerModel)
                            .join(ScorerModel, ScorerModel.id == ScorerVersionModel.scorer_id)
                            .where(
                                ScorerVersionModel.id.in_(
                                    [
                                        UUID(str(item))
                                        for item in scorer_ids_raw
                                        if isinstance(item, str)
                                    ]
                                ),
                                ScorerVersionModel.status == "published",
                                ScorerVersionModel.project_id == project_id.value,
                            )
                        )
                    ).all()
                )
                for scorer_version, scorer in scorer_rows:
                    scorer_configs.append(
                        {
                            "scorer_version_id": str(scorer_version.id),
                            "scorer_type": scorer.scorer_type,
                            "weight": scorer.weight,
                            "threshold": scorer.threshold,
                            "config": dict(scorer_version.config),
                        }
                    )
            cases = list(
                (
                    await session.scalars(
                        select(TestCaseModel)
                        .where(
                            TestCaseModel.dataset_version_id == dataset_version.id,
                        )
                        .order_by(TestCaseModel.sort_order)
                    )
                ).all()
            )
        plugin_snapshot: dict[str, object] = {
            "id": "generic-http",
            "version": "1.0.0",
            "agent_type": agent.agent_type,
            "agent_config": invocation_from_stored_config(stored_agent_config).model_dump(
                mode="json"
            ),
            "agent_metadata": stored_agent_config,
            "environment_config": environment_config,
            "scorer_configs": scorer_configs,
        }
        if profile_snapshot is not None:
            plugin_snapshot["browser_profile_snapshot"] = profile_snapshot
        return RunDefinition(
            project_id=project_id,
            test_plan_version_id=version_id,
            agent_version_id=agent_version.id,
            dataset_version_id=dataset_version.id,
            config_snapshot=dict(plan_version.config),
            plugin_snapshot=plugin_snapshot,
            cases=[
                RunDefinitionCase(
                    test_case_id=case.id,
                    name=case.name,
                    input_snapshot=dict(case.input),
                    assertion_snapshot=list(case.assertions),
                    case_spec_snapshot=build_case_spec_snapshot(_to_test_case(case)),
                    execution_mode=str(case.execution_mode),
                )
                for case in cases
            ],
        )


class SqlAlchemyCaseTrialRuntimeSource(CaseTrialRuntimeSource):
    """Resolve same-project immutable Agent and environment inputs for a case trial."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def load(
        self,
        *,
        project_id: ProjectId,
        agent_version_id: UUID,
        environment_template_id: UUID,
    ) -> CaseTrialRuntime:
        statement = (
            select(AgentVersionModel, AgentModel, EnvironmentTemplateModel)
            .join(AgentModel, AgentModel.id == AgentVersionModel.agent_id)
            .join(
                EnvironmentTemplateModel,
                EnvironmentTemplateModel.id == environment_template_id,
            )
            .where(
                AgentVersionModel.id == agent_version_id,
                AgentVersionModel.status == "published",
                AgentModel.project_id == project_id.value,
                EnvironmentTemplateModel.project_id == project_id.value,
            )
        )
        async with session_scope(self._session_factory) as session:
            row = (await session.execute(statement)).one_or_none()
            if row is None:
                raise ValueError("Published Agent version or project environment was not found")
            agent_version, agent, environment = row
            stored_agent_config = dict(agent_version.config)
            environment_config = dict(environment.config)
            credential_ids_raw = environment_config.get("credential_binding_ids", [])
            credential_ids = (
                [UUID(str(item)) for item in credential_ids_raw]
                if isinstance(credential_ids_raw, list)
                else []
            )
            credential_rows = (
                list(
                    (
                        await session.scalars(
                            select(CredentialBindingModel).where(
                                CredentialBindingModel.project_id == project_id.value,
                                CredentialBindingModel.id.in_(credential_ids),
                            )
                        )
                    ).all()
                )
                if credential_ids
                else []
            )
            if len(credential_rows) != len(set(credential_ids)):
                raise ValueError("Environment references a missing project credential")
            environment_config["credential_bindings"] = secret_free_credential_bindings(
                [
                    {
                        "id": str(item.id),
                        "kind": item.kind,
                        "injection_location": item.injection_location,
                        "injection_name": item.injection_name,
                    }
                    for item in credential_rows
                ]
            )
        return CaseTrialRuntime(
            agent_version_id=agent_version.id,
            config_snapshot={
                "concurrency": 1,
                "case_trial": True,
                "environment_template_id": str(environment_template_id),
            },
            plugin_snapshot={
                "id": "generic-http",
                "version": "1.0.0",
                "agent_type": agent.agent_type,
                "agent_config": invocation_from_stored_config(stored_agent_config).model_dump(
                    mode="json"
                ),
                "agent_metadata": stored_agent_config,
                "environment_config": environment_config,
                "scorer_configs": [],
            },
        )
