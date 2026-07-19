from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.identity.application.ports import LoginThrottleEntry, SessionRecord
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)
from agenttest.modules.identity.infrastructure.persistence.models import (
    LoginThrottleModel,
    UserCredentialModel,
    UserModel,
    UserSessionModel,
)
from agenttest.shared.application.pagination import PageRequest, PageResult
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyUserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_email(self, email: Email) -> User | None:
        async with session_scope(self._session_factory) as session:
            model = await session.scalar(
                select(UserModel).where(UserModel.email_normalized == email.value)
            )
        return _to_user(model)

    async def get_by_id(self, user_id: UserId) -> User | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(UserModel, user_id.value)
        return _to_user(model)

    async def add(self, user: User) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(_to_model(user))

    async def save(self, user: User) -> None:
        async with transaction_scope(self._session_factory) as session:
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
        async with session_scope(self._session_factory) as session:
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
        async with session_scope(self._session_factory) as session:
            count = await session.scalar(
                select(func.count())
                .select_from(UserSessionModel)
                .where(UserSessionModel.user_id == user_id.value)
            )
        return bool(count)

    async def delete(self, user_id: UserId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(delete(UserModel).where(UserModel.id == user_id.value))

    async def update_lockout(self, user: User) -> None:
        """更新登录失败计数和锁定时间。"""
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(UserModel)
                .where(UserModel.id == user.user_id.value)
                .values(
                    failed_login_count=user.failed_login_count,
                    locked_until=user.locked_until,
                    updated_at=func.now(),
                )
            )

    async def list_page(
        self,
        *,
        cursor: UUID | None,
        limit: int,
    ) -> tuple[list[User], UUID | None]:
        statement = select(UserModel).order_by(UserModel.id).limit(limit + 1)
        if cursor is not None:
            statement = statement.where(UserModel.id > cursor)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        page_models = models[:limit]
        items = [user for model in page_models if (user := _to_user(model)) is not None]
        next_cursor = page_models[-1].id if has_more and page_models else None
        return items, next_cursor

    async def count_all(self) -> int:
        async with session_scope(self._session_factory) as session:
            return int(await session.scalar(select(func.count()).select_from(UserModel)) or 0)

    async def list_numbered_page(self, page_request: PageRequest) -> PageResult[User]:
        statement = (
            select(UserModel)
            .order_by(UserModel.id)
            .offset(page_request.offset)
            .limit(page_request.page_size)
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
            total = int(await session.scalar(select(func.count()).select_from(UserModel)) or 0)
        return PageResult(
            items=[user for model in models if (user := _to_user(model)) is not None],
            total=total,
            page=page_request.page,
            page_size=page_request.page_size,
        )


class SqlAlchemyCredentialRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_password_hash(self, user_id: UserId) -> str | None:
        async with session_scope(self._session_factory) as session:
            return await session.scalar(
                select(UserCredentialModel.password_hash).where(
                    UserCredentialModel.user_id == user_id.value
                )
            )

    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None:
        async with transaction_scope(self._session_factory) as session:
            existing_id = await session.scalar(
                select(UserCredentialModel.id).where(UserCredentialModel.user_id == user_id.value)
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
        async with transaction_scope(self._session_factory) as session:
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
        async with session_scope(self._session_factory) as session:
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
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(UserSessionModel)
                .where(
                    UserSessionModel.token_hash == token_hash,
                    UserSessionModel.revoked_at.is_(None),
                )
                .values(revoked_at=revoked_at)
            )

    async def revoke_all_for_user(self, user_id: UserId, revoked_at: datetime) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(UserSessionModel)
                .where(
                    UserSessionModel.user_id == user_id.value,
                    UserSessionModel.revoked_at.is_(None),
                )
                .values(revoked_at=revoked_at)
            )


class SqlAlchemyLoginThrottleRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, key_hash: str) -> LoginThrottleEntry | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(LoginThrottleModel, key_hash)
        return _to_login_throttle(model)

    async def record_failure(
        self,
        key_hash: str,
        *,
        now: datetime,
        window: timedelta,
        max_failures: int,
        blocked_for: timedelta,
    ) -> LoginThrottleEntry:
        async with transaction_scope(self._session_factory) as session:
            dialect = session.get_bind().dialect.name
            insert = postgresql_insert if dialect == "postgresql" else sqlite_insert
            insert_statement = insert(LoginThrottleModel).values(
                key_hash=key_hash,
                failure_count=1,
                window_started_at=now,
                blocked_until=now + blocked_for if max_failures == 1 else None,
                updated_at=now,
            )
            window_expired = LoginThrottleModel.window_started_at <= now - window
            still_blocked = LoginThrottleModel.blocked_until.is_not(None) & (
                LoginThrottleModel.blocked_until > now
            )
            next_count = case(
                (window_expired, 1),
                else_=LoginThrottleModel.failure_count + 1,
            )
            blocked_until = case(
                (still_blocked, LoginThrottleModel.blocked_until),
                (next_count >= max_failures, now + blocked_for),
                else_=None,
            )
            statement: Any = insert_statement.on_conflict_do_update(
                index_elements=[LoginThrottleModel.key_hash],
                set_={
                    "failure_count": case(
                        (still_blocked, LoginThrottleModel.failure_count),
                        else_=next_count,
                    ),
                    "window_started_at": case(
                        (still_blocked, LoginThrottleModel.window_started_at),
                        (window_expired, now),
                        else_=LoginThrottleModel.window_started_at,
                    ),
                    "blocked_until": blocked_until,
                    "updated_at": now,
                },
            ).returning(LoginThrottleModel)
            model = (await session.scalars(statement)).one()
            entry = _to_login_throttle(model)
            assert entry is not None
            return entry

    async def clear(self, key_hashes: tuple[str, ...]) -> None:
        if not key_hashes:
            return
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(LoginThrottleModel).where(LoginThrottleModel.key_hash.in_(key_hashes))
            )

    async def delete_expired(self, cutoff: datetime, *, limit: int = 100) -> int:
        expired = (
            select(LoginThrottleModel.key_hash)
            .where(LoginThrottleModel.updated_at < cutoff)
            .order_by(LoginThrottleModel.updated_at)
            .limit(limit)
        )
        async with transaction_scope(self._session_factory) as session:
            result = await session.execute(
                delete(LoginThrottleModel).where(LoginThrottleModel.key_hash.in_(expired))
            )
            return int(getattr(result, "rowcount", 0) or 0)


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
        failed_login_count=model.failed_login_count,
        locked_until=model.locked_until,
    )


def _to_login_throttle(model: LoginThrottleModel | None) -> LoginThrottleEntry | None:
    if model is None:
        return None
    return LoginThrottleEntry(
        key_hash=model.key_hash,
        failure_count=model.failure_count,
        window_started_at=_utc(model.window_started_at),
        blocked_until=_utc(model.blocked_until) if model.blocked_until else None,
        updated_at=_utc(model.updated_at),
    )


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _to_model(user: User) -> UserModel:
    return UserModel(
        id=user.user_id.value,
        email=user.email.value,
        email_normalized=user.email.value,
        display_name=user.display_name,
        role=user.role.value,
        status=user.status.value,
        must_change_password=user.must_change_password,
        failed_login_count=user.failed_login_count,
        locked_until=user.locked_until,
        created_at=func.now(),
        updated_at=func.now(),
        created_by=None,
        updated_by=None,
    )
