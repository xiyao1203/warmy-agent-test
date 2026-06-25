from hashlib import sha256
from hmac import compare_digest

from agenttest.modules.identity.application.ports import SessionRepository, UserReader
from agenttest.modules.identity.domain.entities import User
from agenttest.shared.domain.clock import Clock


class InvalidSessionError(Exception):
    pass


class CurrentUserQuery:
    def __init__(
        self,
        *,
        users: UserReader,
        sessions: SessionRepository,
        clock: Clock,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._clock = clock

    async def execute(self, session_token: str) -> User:
        token_hash = sha256(session_token.encode()).hexdigest()
        session = await self._sessions.get_by_token_hash(token_hash)
        if session is None or not session.is_valid_at(self._clock.now()):
            raise InvalidSessionError
        user = await self._users.get_by_id(session.user_id)
        if user is None or not user.can_authenticate:
            raise InvalidSessionError
        return user


class CsrfValidator:
    def __init__(self, *, sessions: SessionRepository, clock: Clock) -> None:
        self._sessions = sessions
        self._clock = clock

    async def execute(self, session_token: str, csrf_token: str) -> None:
        session_hash = sha256(session_token.encode()).hexdigest()
        csrf_hash = sha256(csrf_token.encode()).hexdigest()
        session = await self._sessions.get_by_token_hash(session_hash)
        if (
            session is None
            or not session.is_valid_at(self._clock.now())
            or not compare_digest(session.csrf_token_hash, csrf_hash)
        ):
            raise InvalidSessionError
