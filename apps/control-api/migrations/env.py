from __future__ import annotations

import asyncio
from logging.config import fileConfig

from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.audit.infrastructure.persistence.models import AuditLogModel
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.environments.infrastructure.persistence.models import (
    EnvironmentTemplateModel,
)
from agenttest.modules.identity.infrastructure.persistence.models import (
    UserCredentialModel,
    UserModel,
    UserSessionModel,
)
from agenttest.modules.projects.infrastructure.persistence.models import (
    ProjectMemberModel,
    ProjectModel,
)
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunEventModel,
    RunModel,
)
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.infrastructure.database import Base
from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

_MODELS = (
    AgentModel,
    AgentVersionModel,
    AuditLogModel,
    DatasetModel,
    DatasetVersionModel,
    EnvironmentTemplateModel,
    ProjectMemberModel,
    ProjectModel,
    RunCaseModel,
    RunEventModel,
    RunModel,
    TestCaseModel,
    TestPlanModel,
    TestPlanVersionModel,
    UserCredentialModel,
    UserModel,
    UserSessionModel,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_sync_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # 支持 AGENTTEST_DATABASE_URL 或 DATABASE_URL 环境变量覆盖
    import os

    db_url = (
        os.environ.get("AGENTTEST_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )
    config.set_main_option("sqlalchemy.url", db_url)

    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(run_sync_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
