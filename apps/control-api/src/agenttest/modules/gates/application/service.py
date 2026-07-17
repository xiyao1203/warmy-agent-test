from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.gates.application.evaluate import GateEvidence, evaluate_evidence
from agenttest.modules.gates.domain.entities import GateResult, ReleaseGate, ReleaseGateId
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class GateRepository(Protocol):
    async def get_by_id_and_project(
        self, gate_id: ReleaseGateId, project_id: UUID
    ) -> ReleaseGate | None: ...

    async def list_by_project(self, project_id: UUID, *, limit: int = 50) -> list[ReleaseGate]: ...

    async def add(self, gate: ReleaseGate) -> None: ...

    async def save(self, gate: ReleaseGate) -> None: ...

    async def delete(self, gate_id: ReleaseGateId) -> None: ...


class GateEvidencePort(Protocol):
    async def load(self, project_id: UUID, run_id: UUID) -> GateEvidence | None: ...

    async def record(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        actor_id: UUID,
        evidence: GateEvidence,
        passed: bool,
        failures: list[str],
        experiment_id: UUID | None,
    ) -> UUID: ...


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class GateNotFound(Exception):
    pass


class GateEvidenceNotFound(Exception):
    pass


class GateValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class GateEvaluation:
    gate: ReleaseGate
    decision_id: UUID
    evidence: GateEvidence
    result: GateResult


class GateService:
    def __init__(
        self,
        *,
        gates: GateRepository,
        evidence: GateEvidencePort,
        project_access: ProjectAccessPort,
    ) -> None:
        self._gates = gates
        self._evidence = evidence
        self._project_access = project_access

    async def list_gates(self, actor: User, project_id: UUID) -> list[ReleaseGate]:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._gates.list_by_project(project_id)

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        success_rate_threshold: float,
        critical_cases: list[str],
        cost_limit: float | None,
        security_threshold: float,
    ) -> ReleaseGate:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        try:
            gate = ReleaseGate.create(
                project_id=project_id,
                name=name,
                success_rate_threshold=success_rate_threshold,
                critical_cases=critical_cases,
                cost_limit=cost_limit,
                security_threshold=security_threshold,
            )
        except ValueError as error:
            raise GateValidationError(str(error)) from error
        await self._gates.add(gate)
        return gate

    async def get(self, actor: User, project_id: UUID, gate_id: UUID) -> ReleaseGate:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._gate(project_id, gate_id)

    async def evaluate(
        self,
        actor: User,
        project_id: UUID,
        gate_id: UUID,
        *,
        run_id: UUID,
        experiment_id: UUID | None,
    ) -> GateEvaluation:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        gate = await self._gate(project_id, gate_id)
        evidence = await self._evidence.load(project_id, run_id)
        if evidence is None:
            raise GateEvidenceNotFound
        result = evaluate_evidence(gate, evidence)
        decision_id = await self._evidence.record(
            project_id=project_id,
            gate_id=gate_id,
            actor_id=actor.user_id.value,
            evidence=evidence,
            passed=result.passed,
            failures=result.failures,
            experiment_id=experiment_id,
        )
        return GateEvaluation(gate, decision_id, evidence, result)

    async def exempt(self, actor: User, project_id: UUID, gate_id: UUID) -> ReleaseGate:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        gate = await self._gate(project_id, gate_id)
        gate.toggle()
        await self._gates.save(gate)
        return gate

    async def delete(self, actor: User, project_id: UUID, gate_id: UUID) -> None:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        await self._gate(project_id, gate_id)
        await self._gates.delete(ReleaseGateId(gate_id))

    async def _gate(self, project_id: UUID, gate_id: UUID) -> ReleaseGate:
        gate = await self._gates.get_by_id_and_project(ReleaseGateId(gate_id), project_id)
        if gate is None:
            raise GateNotFound
        return gate
