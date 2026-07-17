"""超级 Agent 到专业控制台公开应用能力的适配层。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from agenttest.modules.agents.public import (
    AgentVersionId,
)
from agenttest.modules.experiments.public import Experiment, ExperimentId
from agenttest.modules.gates.public import ReleaseGateId, evaluate_evidence
from agenttest.modules.scorers.public import Scorer, ScorerId, ScorerType
from agenttest.modules.security.public import (
    ScanStatus,
    SecurityScan,
    create_scanner,
    validate_agent_endpoint,
)
from agenttest.modules.test_agent.adapters.platform_projection import (
    _artifact,
    _created,
    _experiment,
    _gate,
    _optional,
    _resource_ref,
    _review,
    _scorer,
    _security_scan,
    _summary_item,
)
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.shared.application.core_summaries import CoreSummaryReader
from agenttest.shared.application.resource_reference import (
    ResourceType,
)


class PlatformQualityCapabilities:
    def __init__(
        self,
        *,
        scorers,
        experiments,
        reviews,
        gates,
        security,
        agents,
        promptfoo_bin: str,
        allow_private_security_targets: bool,
        gate_evidence,
        summaries: CoreSummaryReader | None = None,
    ) -> None:
        self._scorers = scorers
        self._experiments = experiments
        self._reviews = reviews
        self._gates = gates
        self._security = security
        self._agents = agents
        self._promptfoo_bin = promptfoo_bin
        self._allow_private_security_targets = allow_private_security_targets
        self._gate_evidence = gate_evidence
        self._summaries = summaries

    async def execute(
        self,
        capability: str,
        context: OrchestrationContext,
        values: dict[str, Any],
    ) -> dict[str, object]:
        project_id = context.project_id
        if capability == "scorers.list":
            items, _ = await self._scorers.list_by_project(project_id)
            scorer_summaries = (
                await self._summaries.scorers(
                    project_id.value, [item.scorer_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _scorer(item),
                        scorer_summaries.get(item.scorer_id.value),
                        _resource_ref(
                            ResourceType.SCORER,
                            item.scorer_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "scorers.create":
            config = dict(values["config"])
            item = Scorer.create(
                scorer_id=ScorerId.new(),
                project_id=project_id,
                name=str(values["name"]),
                scorer_type=ScorerType(str(config.pop("scorer_type", "rule"))),
                weight=float(config.pop("weight", 1)),
                threshold=float(config.pop("threshold", 0.8)),
                config_json=config,
                description=_optional(values.get("description")),
            )
            await self._scorers.add(item)
            return _created("scorer", item.scorer_id.value, _scorer(item))
        if capability == "experiments.list":
            items = await self._experiments.list_by_project(project_id)
            experiment_summaries = (
                await self._summaries.experiments(
                    project_id.value, [item.experiment_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _experiment(item),
                        experiment_summaries.get(item.experiment_id.value),
                        _resource_ref(
                            ResourceType.EXPERIMENT,
                            item.experiment_id.value,
                            project_id.value,
                            item.name,
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "experiments.create":
            experiment = Experiment.create(
                experiment_id=ExperimentId.new(),
                project_id=project_id,
                name=str(values["name"]),
                run_a_id=UUID(str(values["baseline_run_id"])),
                run_b_id=UUID(str(values["candidate_run_id"])),
                description=_optional(values.get("description")),
            )
            await self._experiments.add(experiment)
            return _created(
                "experiment",
                experiment.experiment_id.value,
                _experiment(experiment),
            )
        if capability == "security_scans.list":
            items = await self._security.list_by_project(project_id.value)
            scan_summaries = (
                await self._summaries.security_scans(
                    project_id.value, [item.scan_id for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _security_scan(item),
                        scan_summaries.get(item.scan_id),
                        _resource_ref(
                            ResourceType.SECURITY_SCAN,
                            item.scan_id,
                            project_id.value,
                            f"Security scan {str(item.scan_id)[:8]}",
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "security_scans.start":
            version = await self._agents.get_version.execute(
                context.actor,
                AgentVersionId(UUID(str(values["agent_version_id"]))),
            )
            agent = await self._agents.get_agent.execute(context.actor, version.agent_id)
            if agent.project_id != project_id:
                raise ValueError("Agent version does not exist in project")
            endpoint = version.config.api_url
            validate_agent_endpoint(
                endpoint,
                allow_private_network=self._allow_private_security_targets,
            )
            scan = SecurityScan.create(
                project_id=project_id.value,
                scan_type="full",
                agent_version_id=version.version_id.value,
                run_id=UUID(str(values["run_id"])) if values.get("run_id") else None,
                security_profile_id=(
                    UUID(str(values["security_profile_id"]))
                    if values.get("security_profile_id")
                    else None
                ),
            )
            await self._security.add(scan)
            scan.status = ScanStatus.RUNNING
            await self._security.save(scan)
            try:
                findings = await create_scanner(self._promptfoo_bin).run_scan(
                    agent_endpoint=endpoint, scan_type="full"
                )
                scan.complete(findings)
            except Exception as error:
                scan.fail(str(error))
                await self._security.save(scan)
                raise
            await self._security.save(scan)
            return _created("security_scan", scan.scan_id, _security_scan(scan))
        if capability == "reviews.list":
            items, total = await self._reviews.list_by_project(project_id)
            review_summaries = (
                await self._summaries.reviews(
                    project_id.value, [item.task_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _review(item),
                        review_summaries.get(item.task_id.value),
                        _resource_ref(
                            ResourceType.REVIEW,
                            item.task_id.value,
                            project_id.value,
                            f"Review {str(item.task_id.value)[:8]}",
                            status=item.status.value,
                        ),
                    )
                    for item in items
                ],
                "total": total,
            }
        if capability == "reviews.enqueue":
            items = await self._reviews.auto_enqueue_low_confidence(
                project_id,
                str(values["run_id"]),
                float(values["confidence_threshold"]),
            )
            return {
                "items": [_review(item) for item in items],
                "artifacts": [_artifact("review_task", item.task_id.value) for item in items],
            }
        if capability == "release_gates.list":
            items = await self._gates.list_by_project(project_id.value)
            gate_summaries = (
                await self._summaries.gates(
                    project_id.value, [item.gate_id.value for item in items]
                )
                if self._summaries
                else {}
            )
            return {
                "items": [
                    _summary_item(
                        _gate(item),
                        gate_summaries.get(item.gate_id.value),
                        _resource_ref(
                            ResourceType.RELEASE_GATE,
                            item.gate_id.value,
                            project_id.value,
                            item.name,
                        ),
                    )
                    for item in items
                ]
            }
        if capability == "release_gates.evaluate":
            gate = await self._gates.get_by_id_and_project(
                ReleaseGateId(UUID(str(values["gate_id"]))), project_id.value
            )
            if gate is None:
                raise ValueError("Release gate does not exist in project")
            run_id = UUID(str(values["run_id"]))
            evidence = await self._gate_evidence.load(project_id.value, run_id)
            if evidence is None:
                raise ValueError("Run does not exist in project")
            result = evaluate_evidence(gate, evidence)
            decision_id = await self._gate_evidence.record(
                project_id=project_id.value,
                gate_id=gate.gate_id.value,
                actor_id=context.actor.user_id.value,
                evidence=evidence,
                passed=result.passed,
                failures=result.failures,
                experiment_id=None,
            )
            return _created(
                "release_decision",
                decision_id,
                {**result.to_dict(), "run_id": str(run_id)},
                relation="evaluated",
            )
        raise KeyError(f"Unsupported platform capability: {capability}")
