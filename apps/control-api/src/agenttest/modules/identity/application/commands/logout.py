from hashlib import sha256

from agenttest.modules.identity.application.ports import SessionRepository
from agenttest.shared.domain.clock import Clock


class LogoutHandler:
    def __init__(self, *, sessions: SessionRepository, clock: Clock) -> None:
        self._sessions = sessions
        self._clock = clock

    async def execute(self, session_token: str) -> None:
        token_hash = sha256(session_token.encode()).hexdigest()
        await self._sessions.revoke_by_token_hash(token_hash, self._clock.now())
