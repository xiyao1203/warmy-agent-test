from hashlib import sha256

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.identity.application.ports import SessionRepository
from agenttest.shared.domain.clock import Clock


class LogoutHandler:
    def __init__(
        self,
        *,
        sessions: SessionRepository,
        clock: Clock,
        audit: AuditWriter | None = None,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._audit = audit

    async def execute(self, session_token: str) -> None:
        token_hash = sha256(session_token.encode()).hexdigest()
        session = await self._sessions.get_by_token_hash(token_hash)
        await self._sessions.revoke_by_token_hash(token_hash, self._clock.now())
        if self._audit is not None and session is not None:
            await self._audit.record(
                actor_user_id=session.user_id,
                action="identity.logout",
                object_type="session",
                object_id=session.session_id,
                project_id=None,
                changes={},
                source_ip=None,
            )
