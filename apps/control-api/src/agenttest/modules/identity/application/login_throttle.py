from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256

from agenttest.modules.identity.application.ports import (
    LoginThrottleRepository,
)
from agenttest.shared.domain.clock import Clock


@dataclass(frozen=True, slots=True)
class LoginThrottlePolicy:
    window: timedelta
    max_failures: int
    blocked_for: timedelta

    def __post_init__(self) -> None:
        if self.window <= timedelta(0):
            raise ValueError("Login throttle window must be positive")
        if self.max_failures <= 0:
            raise ValueError("Login throttle max failures must be positive")
        if self.blocked_for <= timedelta(0):
            raise ValueError("Login throttle block duration must be positive")


class LoginThrottle:
    def __init__(
        self,
        *,
        repository: LoginThrottleRepository,
        clock: Clock,
        policy: LoginThrottlePolicy,
        pepper: bytes,
    ) -> None:
        if not pepper:
            raise ValueError("Login throttle pepper must not be empty")
        self._repository = repository
        self._clock = clock
        self._policy = policy
        self._pepper = pepper

    def key_hashes(self, email: str, source_ip: str) -> tuple[str, str]:
        normalized_email = email.strip().casefold()
        return (
            self._digest(f"account\0{normalized_email}"),
            self._digest(f"account-ip\0{normalized_email}\0{source_ip}"),
        )

    async def is_blocked(self, email: str, source_ip: str) -> bool:
        now = self._clock.now()
        for key_hash in self.key_hashes(email, source_ip):
            entry = await self._repository.get(key_hash)
            if entry is not None and _after(entry.blocked_until, now):
                return True
        return False

    async def record_failure(self, email: str, source_ip: str) -> bool:
        now = self._clock.now()
        blocked = False
        for key_hash in self.key_hashes(email, source_ip):
            entry = await self._repository.record_failure(
                key_hash,
                now=now,
                window=self._policy.window,
                max_failures=self._policy.max_failures,
                blocked_for=self._policy.blocked_for,
            )
            blocked = blocked or _after(entry.blocked_until, now)
        return blocked

    async def clear_success(self, email: str, source_ip: str) -> None:
        await self._repository.clear(self.key_hashes(email, source_ip))

    def _digest(self, value: str) -> str:
        return hmac.new(self._pepper, value.encode(), sha256).hexdigest()


def _after(value: datetime | None, now: datetime) -> bool:
    if value is None:
        return False
    if value.tzinfo is None and now.tzinfo is not None:
        value = value.replace(tzinfo=now.tzinfo)
    return value > now
