from dataclasses import dataclass
from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.identity.application.ports import (
    CredentialReader,
    LoginThrottlePort,
    PasswordHasher,
    SessionRecord,
    SessionRepository,
    UserReader,
)
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email
from agenttest.shared.domain.clock import Clock


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: Email
    password: str
    source_ip: str = "0.0.0.0"


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User
    session_token: str
    csrf_token: str


class LoginHandler:
    def __init__(
        self,
        *,
        users: UserReader,
        credentials: CredentialReader,
        sessions: SessionRepository,
        password_hasher: PasswordHasher,
        clock: Clock,
        session_ttl: timedelta,
        throttle: LoginThrottlePort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._users = users
        self._credentials = credentials
        self._sessions = sessions
        self._password_hasher = password_hasher
        self._clock = clock
        self._session_ttl = session_ttl
        self._throttle = throttle
        self._audit = audit
        self._dummy_password_hash = password_hasher.hash(token_urlsafe(32))

    async def execute(self, command: LoginCommand) -> LoginResult:
        if await self._throttle.is_blocked(command.email.value, command.source_ip):
            raise InvalidCredentialsError
        user = await self._users.get_by_email(command.email)
        password_hash = (
            await self._credentials.get_password_hash(user.user_id) if user is not None else None
        )
        password_verified = self._password_hasher.verify(
            password_hash or self._dummy_password_hash,
            command.password,
        )
        if (
            user is None
            or password_hash is None
            or not user.can_authenticate
            or not password_verified
        ):
            await self._throttle.record_failure(command.email.value, command.source_ip)
            if self._audit is not None:
                await self._audit.record(
                    actor_user_id=user.user_id if user is not None else None,
                    action="identity.login.failed",
                    object_type="user",
                    object_id=user.user_id.value if user is not None else None,
                    project_id=None,
                    changes={"email": {"attempted": command.email.value}},
                    source_ip=command.source_ip,
                )
            raise InvalidCredentialsError

        await self._throttle.clear_success(command.email.value, command.source_ip)
        user.reset_failed_logins()
        await self._users.update_lockout(user)
        now = self._clock.now()
        session_token = token_urlsafe(32)
        csrf_token = token_urlsafe(32)
        await self._sessions.add(
            SessionRecord(
                user_id=user.user_id,
                token_hash=_hash_token(session_token),
                csrf_token_hash=_hash_token(csrf_token),
                expires_at=now + self._session_ttl,
                revoked_at=None,
                created_at=now,
            )
        )
        if self._audit is not None:
            await self._audit.record(
                actor_user_id=user.user_id,
                action="identity.login.succeeded",
                object_type="user",
                object_id=user.user_id.value,
                project_id=None,
                changes={},
                source_ip=command.source_ip,
            )
        return LoginResult(
            user=user,
            session_token=session_token,
            csrf_token=csrf_token,
        )


def _hash_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


class NoopLoginThrottle:
    async def is_blocked(self, email: str, source_ip: str) -> bool:
        return False

    async def record_failure(self, email: str, source_ip: str) -> bool:
        return False

    async def clear_success(self, email: str, source_ip: str) -> None:
        return None
