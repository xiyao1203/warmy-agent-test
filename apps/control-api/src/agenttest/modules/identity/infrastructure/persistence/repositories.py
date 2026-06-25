from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
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

    async def add(self, user: User) -> None:
        async with self._session_factory.begin() as session:
            session.add(_to_model(user))

    async def save(self, user: User) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(
                update(UserModel)
                .where(UserModel.id == user.user_id.value)
                .values(
                    email=user.email.value,
                    email_normalized=user.email.value,
                    display_name=user.display_name,
                    role=user.role.value,
                    status=user.status.value,
                    must_change_password=user.must_change_password,
                    updated_at=func.now(),
                )
            )

    async def count_active_super_admins(self) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(UserModel)
                .where(
                    UserModel.role == SystemRole.SUPER_ADMIN.value,
                    UserModel.status == UserStatus.ACTIVE.value,
                )
            )
        return int(count or 0)

    async def has_historical_activity(self, user_id: UserId) -> bool:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(UserSessionModel)
                .where(UserSessionModel.user_id == user_id.value)
            )
        return bool(count)

    async def delete(self, user_id: UserId) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(delete(UserModel).where(UserModel.id == user_id.value))

    async def list_page(
        self,
        *,
        cursor: UUID | None,
        limit: int,
    ) -> tuple[list[User], UUID | None]:
        statement = select(UserModel).order_by(UserModel.id).limit(limit + 1)
        if cursor is not None:
            statement = statement.where(UserModel.id > cursor)
        async with self._session_factory() as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        page_models = models[:limit]
        items = [user for model in page_models if (user := _to_user(model)) is not None]
        next_cursor = page_models[-1].id if has_more and page_models else None
        return items, next_cursor


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

    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None:
        async with self._session_factory.begin() as session:
            existing_id = await session.scalar(
                select(UserCredentialModel.id).where(
                    UserCredentialModel.user_id == user_id.value
                )
            )
            if existing_id is None:
                session.add(
                    UserCredentialModel(
                        id=uuid4(),
                        user_id=user_id.value,
                        password_hash=password_hash,
                        created_at=func.now(),
                        updated_at=func.now(),
                    )
                )
            else:
                await session.execute(
                    update(UserCredentialModel)
                    .where(UserCredentialModel.user_id == user_id.value)
                    .values(password_hash=password_hash, updated_at=func.now())
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

    async def revoke_all_for_user(self, user_id: UserId, revoked_at: datetime) -> None:
        async with self._session_factory.begin() as session:
            await session.execute(
                update(UserSessionModel)
                .where(
                    UserSessionModel.user_id == user_id.value,
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


def _to_model(user: User) -> UserModel:
    return UserModel(
        id=user.user_id.value,
        email=user.email.value,
        email_normalized=user.email.value,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        must_change_password=user.must_change_password,
        created_at=func.now(),
        updated_at=func.now(),
        created_by=None,
        updated_by=None,
    )
