from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.identity.application.ports import SessionRecord
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)
from agenttest.modules.identity.infrastructure.persistence.models import (
    UserCredentialModel,
    UserModel,
    UserSessionModel,
)


class SqlAlchemyUserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_email(self, email: Email) -> User | None:
        async with self._session_factory() as session:
            model = await session.scalar(
                select(UserModel).where(UserModel.email_normalized == email.value)
            )
        return _to_user(model)

    async def get_by_id(self, user_id: UserId) -> User | None:
        async with self._session_factory() as session:
            model = await session.get(UserModel, user_id.value)
        return _to_user(model)


class SqlAlchemyCredentialRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_password_hash(self, user_id: UserId) -> str | None:
        async with self._session_factory() as session:
            return await session.scalar(
                select(UserCredentialModel.password_hash).where(
                    UserCredentialModel.user_id == user_id.value
                )
            )


class SqlAlchemySessionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, session_record: SessionRecord) -> None:
        async with self._session_factory.begin() as session:
            session.add(
                UserSessionModel(
                    id=session_record.session_id,
                    user_id=session_record.user_id.value,
                    token_hash=session_record.token_hash,
                    csrf_token_hash=session_record.csrf_token_hash,
                    expires_at=session_record.expires_at,
                    revoked_at=session_record.revoked_at,
                    created_at=session_record.created_at,
                    source_ip=None,
                    user_agent=None,
                )
            )

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        async with self._session_factory() as session:
            model = await session.scalar(
                select(UserSessionModel).where(UserSessionModel.token_hash == token_hash)
            )
        if model is None:
            return None
        return SessionRecord(
            session_id=model.id,
            user_id=UserId(model.user_id),
            token_hash=model.token_hash,
            csrf_token_hash=model.csrf_token_hash,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            created_at=model.created_at,
        )

    async def revoke_by_token_hash(self, token_hash: str, revoked_at: datetime) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(
                update(UserSessionModel)
                .where(
                    UserSessionModel.token_hash == token_hash,
                    UserSessionModel.revoked_at.is_(None),
                )
                .values(revoked_at=revoked_at)
            )


def _to_user(model: UserModel | None) -> User | None:
    if model is None:
        return None
    return User(
        user_id=UserId(model.id),
        email=Email(model.email_normalized),
        display_name=model.display_name,
        role=SystemRole(model.role),
        status=UserStatus(model.status),
        must_change_password=model.must_change_password,
    )
