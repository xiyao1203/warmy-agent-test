from dataclasses import asdict
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.environments.application.credentials import CredentialBindingRecord
from agenttest.modules.environments.infrastructure.persistence.models import CredentialBindingModel


class SqlAlchemyCredentialRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list(self, project_id: UUID) -> list[CredentialBindingRecord]:
        async with self._session_factory() as session:
            rows = list(
                (
                    await session.scalars(
                        select(CredentialBindingModel)
                        .where(CredentialBindingModel.project_id == project_id)
                        .order_by(CredentialBindingModel.created_at.desc())
                    )
                ).all()
            )
        return [_to_record(item) for item in rows]

    async def add(self, item: CredentialBindingRecord) -> None:
        async with self._session_factory() as session:
            session.add(CredentialBindingModel(**asdict(item)))
            await session.commit()

    async def get_many(
        self, project_id: UUID, credential_ids: list[UUID]
    ) -> list[CredentialBindingRecord]:
        if not credential_ids:
            return []
        async with self._session_factory() as session:
            rows = list(
                (
                    await session.scalars(
                        select(CredentialBindingModel).where(
                            CredentialBindingModel.project_id == project_id,
                            CredentialBindingModel.id.in_(credential_ids),
                        )
                    )
                ).all()
            )
        return [_to_record(item) for item in rows]

    async def delete(self, project_id: UUID, credential_id: UUID) -> bool:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(CredentialBindingModel.id).where(
                    CredentialBindingModel.id == credential_id,
                    CredentialBindingModel.project_id == project_id,
                )
            )
            if existing is None:
                return False
            await session.execute(
                delete(CredentialBindingModel).where(CredentialBindingModel.id == credential_id)
            )
            await session.commit()
            return True


def _to_record(item: CredentialBindingModel) -> CredentialBindingRecord:
    return CredentialBindingRecord(
        id=item.id,
        project_id=item.project_id,
        alias=item.alias,
        kind=item.kind,
        injection_location=item.injection_location,
        injection_name=item.injection_name,
        encrypted_value=item.encrypted_value,
        masked_hint=item.masked_hint,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
