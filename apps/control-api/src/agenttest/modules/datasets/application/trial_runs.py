"""Create an immutable, project-scoped single-case trial Run."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol, cast
from uuid import UUID

from agenttest.modules.datasets.application.commands import CreateCaseTrialRunCommand
from agenttest.modules.datasets.application.contracts import build_case_spec_snapshot
from agenttest.modules.datasets.application.ports import ProjectAccessPort
from agenttest.modules.datasets.domain.entities import TestCase, TestCaseId
from agenttest.modules.datasets.domain.repositories import (
    DatasetRepository,
    DatasetVersionRepository,
    TestCaseRepository,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import (
    Run,
    RunCase,
    RunCaseId,
    RunId,
    RunIdempotencyConflict,
    RunIdempotencyKeyExists,
    RunOrchestrator,
    RunRepository,
    RunType,
)


@dataclass(frozen=True, slots=True)
class CaseTrialRuntime:
    agent_version_id: UUID
    config_snapshot: dict[str, object]
    plugin_snapshot: dict[str, object]


class CaseTrialRuntimeSource(Protocol):
    async def load(
        self,
        *,
        project_id: ProjectId,
        agent_version_id: UUID,
        environment_template_id: UUID,
    ) -> CaseTrialRuntime: ...


@dataclass(frozen=True, slots=True)
class CreateCaseTrialRunResult:
    run: Run
    created: bool


class CreateCaseTrialRunHandler:
    def __init__(
        self,
        *,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        cases: TestCaseRepository,
        runs: RunRepository,
        project_access: ProjectAccessPort,
        runtime_source: CaseTrialRuntimeSource,
        orchestrator: RunOrchestrator,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._cases = cases
        self._runs = runs
        self._project_access = project_access
        self._runtime_source = runtime_source
        self._orchestrator = orchestrator

    async def execute(
        self,
        actor: User,
        command: CreateCaseTrialRunCommand,
    ) -> CreateCaseTrialRunResult:
        key = command.idempotency_key.strip()
        if not key:
            raise ValueError("Idempotency-Key is required")
        case, dataset_project_id = await self._resolve_case(command.case_id)
        if dataset_project_id != command.project_id:
            raise LookupError("Test case was not found")
        await self._project_access.ensure_editor(actor, command.project_id)

        issues = case.readiness_issues()
        if issues:
            raise ValueError(issues[0][2])
        snapshot = build_case_spec_snapshot(case)
        runtime = await self._runtime_source.load(
            project_id=command.project_id,
            agent_version_id=command.agent_version_id,
            environment_template_id=command.environment_template_id,
        )
        request_fingerprint = _trial_request_fingerprint(
            project_id=command.project_id,
            case=case,
            agent_version_id=runtime.agent_version_id,
            environment_template_id=command.environment_template_id,
            snapshot=snapshot,
        )
        existing = await self._runs.get_by_idempotency_key(command.project_id, key)
        if existing is not None:
            return _reuse_exact_trial(existing, case, request_fingerprint)
        await self._orchestrator.ensure_available()

        config_snapshot = {
            **runtime.config_snapshot,
            "case_trial_request_fingerprint": request_fingerprint,
        }
        run = Run.create_case_trial(
            run_id=RunId.new(),
            project_id=command.project_id,
            source_test_case_id=case.case_id.value,
            agent_version_id=runtime.agent_version_id,
            dataset_version_id=case.dataset_version_id.value,
            idempotency_key=key,
            created_by=actor.user_id,
            config_snapshot=config_snapshot,
            plugin_snapshot=runtime.plugin_snapshot,
        )
        run_case = RunCase.create(
            run_case_id=RunCaseId.new(),
            run_id=run.run_id,
            test_case_id=case.case_id.value,
            name=case.name,
            input_snapshot=cast(dict[str, object], snapshot["input"]),
            assertion_snapshot=cast(
                list[dict[str, object]],
                snapshot["assertions"],
            ),
            case_spec_snapshot=snapshot,
            execution_mode=case.execution_mode.value,
        )
        try:
            await self._runs.add(run, [run_case])
        except RunIdempotencyKeyExists:
            winner = await self._runs.get_by_idempotency_key(command.project_id, key)
            if winner is None:
                raise RuntimeError(
                    "Run idempotency conflict was not visible after transaction rollback"
                ) from None
            return _reuse_exact_trial(winner, case, request_fingerprint)
        workflow_id = await self._orchestrator.start(run, [run_case])
        run.start(workflow_id)
        await self._runs.save(run)
        return CreateCaseTrialRunResult(run=run, created=True)

    async def _resolve_case(self, case_id: TestCaseId) -> tuple[TestCase, ProjectId]:
        case = await self._cases.get_by_id(case_id)
        if case is None:
            raise LookupError("Test case was not found")
        version = await self._versions.get_by_id(case.dataset_version_id)
        if version is None:
            raise LookupError("Dataset version was not found")
        dataset = await self._datasets.get_by_id(version.dataset_id)
        if dataset is None:
            raise LookupError("Dataset was not found")
        return case, dataset.project_id


def _trial_request_fingerprint(
    *,
    project_id: ProjectId,
    case: TestCase,
    agent_version_id: UUID,
    environment_template_id: UUID,
    snapshot: dict[str, object],
) -> str:
    canonical = json.dumps(
        {
            "project_id": str(project_id.value),
            "case_id": str(case.case_id.value),
            "agent_version_id": str(agent_version_id),
            "environment_template_id": str(environment_template_id),
            "case_spec": snapshot,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=str,
    ).encode()
    return sha256(canonical).hexdigest()


def _reuse_exact_trial(
    existing: Run,
    case: TestCase,
    request_fingerprint: str,
) -> CreateCaseTrialRunResult:
    if (
        existing.run_type is not RunType.CASE_TRIAL
        or existing.source_test_case_id != case.case_id.value
        or existing.config_snapshot.get("case_trial_request_fingerprint") != request_fingerprint
    ):
        raise RunIdempotencyConflict("Idempotency-Key is already used by a different trial request")
    return CreateCaseTrialRunResult(run=existing, created=False)
