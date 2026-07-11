from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.domain.invocation import invocation_from_stored_config
from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
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
        return RunDefinition(
            project_id=project_id,
            test_plan_version_id=version_id,
            agent_version_id=agent_version.id,
            dataset_version_id=dataset_version.id,
            config_snapshot=dict(plan_version.config),
            plugin_snapshot={
                "id": "generic-http",
                "version": "1.0.0",
                "agent_type": agent.agent_type,
                "agent_config": invocation_from_stored_config(
                    dict(agent_version.config)
                ).model_dump(mode="json"),
                "agent_metadata": dict(agent_version.config),
                "environment_config": environment_config,
                "scorer_configs": scorer_configs,
            },
            cases=[
                RunDefinitionCase(
                    test_case_id=case.id,
                    name=case.name,
                    input_snapshot=dict(case.input),
                    assertion_snapshot=list(case.assertions),
                    execution_mode=str(case.execution_mode),
                )
                for case in cases
            ],
        )
