"""TestAccount 仓库 SQLAlchemy 实现。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.test_accounts.domain.entities import (
    TestAccount,
    TestAccountId,
)
from agenttest.modules.test_accounts.infrastructure.persistence.models import (
    TestAccountModel,
)


class SqlAlchemyTestAccountRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def get_by_id_and_project(
        self, account_id: TestAccountId, project_id: UUID,
    ) -> TestAccount | None:
        async with self._session_factory() as session:
            row = await session.get(TestAccountModel, account_id.value)
            if row is None or row.project_id != project_id:
                return None
            return _to_entity(row)

    async def list_by_project(
        self, project_id: UUID, *, limit: int = 50,
    ) -> list[TestAccount]:
        from sqlalchemy import select

        async with self._session_factory() as session:
            stmt = (
                select(TestAccountModel)
                .where(TestAccountModel.project_id == project_id)
                .order_by(TestAccountModel.created_at.desc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_to_entity(r) for r in rows]

    async def add(self, account: TestAccount) -> None:
        async with self._session_factory() as session:
            session.add(_to_model(account))
            await session.commit()

    async def save(self, account: TestAccount) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    "UPDATE test_accounts SET name=:n, username=:u, "
                    "credential_encrypted=:ce, account_type=:at, enabled=:e, "
                    "description=:d, environment_template_id=:eti, "
                    "updated_at=:ua WHERE id=:id"
                ),
                {
                    "id": account.account_id.value,
                    "n": account.name,
                    "u": account.username,
                    "ce": account.credential_encrypted,
                    "at": account.account_type,
                    "e": account.enabled,
                    "d": account.description,
                    "eti": account.environment_template_id,
                    "ua": account.updated_at,
                },
            )
            await session.commit()

    async def delete(self, account_id: TestAccountId) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM test_accounts WHERE id=:id"),
                {"id": account_id.value},
            )
            await session.commit()


def _to_model(a: TestAccount) -> TestAccountModel:
    return TestAccountModel(
        id=a.account_id.value,
        project_id=a.project_id,
        name=a.name,
        username=a.username,
        credential_encrypted=a.credential_encrypted,
        account_type=a.account_type,
        enabled=a.enabled,
        created_at=a.created_at,
        updated_at=a.updated_at,
        description=a.description,
        environment_template_id=a.environment_template_id,
    )


def _to_entity(row: TestAccountModel) -> TestAccount:
    return TestAccount(
        account_id=TestAccountId(row.id),
        project_id=row.project_id,
        name=row.name,
        username=row.username,
        credential_encrypted=row.credential_encrypted,
        account_type=row.account_type,
        enabled=row.enabled,
        created_at=row.created_at,
        updated_at=row.updated_at,
        description=row.description,
        environment_template_id=row.environment_template_id,
    )
