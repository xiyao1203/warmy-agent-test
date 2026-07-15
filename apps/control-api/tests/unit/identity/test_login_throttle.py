from __future__ import annotations

import hmac
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from agenttest.modules.identity.application.login_throttle import (
    LoginThrottle,
    LoginThrottlePolicy,
)
from agenttest.modules.identity.application.ports import LoginThrottleEntry

NOW = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
POLICY = LoginThrottlePolicy(
    window=timedelta(minutes=15),
    max_failures=8,
    blocked_for=timedelta(minutes=30),
)


class FrozenClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


class FakeThrottleRepository:
    def __init__(self) -> None:
        self.entries: dict[str, LoginThrottleEntry] = {}
        self.cleared: list[tuple[str, ...]] = []

    async def get(self, key_hash: str) -> LoginThrottleEntry | None:
        return self.entries.get(key_hash)

    async def record_failure(
        self,
        key_hash: str,
        *,
        now: datetime,
        window: timedelta,
        max_failures: int,
        blocked_for: timedelta,
    ) -> LoginThrottleEntry:
        current = self.entries.get(key_hash)
        if current is None or current.window_started_at <= now - window:
            failure_count = 1
            window_started_at = now
        elif current.blocked_until is not None and current.blocked_until > now:
            return current
        else:
            failure_count = current.failure_count + 1
            window_started_at = current.window_started_at
        blocked_until = now + blocked_for if failure_count >= max_failures else None
        entry = LoginThrottleEntry(
            key_hash=key_hash,
            failure_count=failure_count,
            window_started_at=window_started_at,
            blocked_until=blocked_until,
            updated_at=now,
        )
        self.entries[key_hash] = entry
        return entry

    async def clear(self, key_hashes: tuple[str, ...]) -> None:
        self.cleared.append(key_hashes)
        for key_hash in key_hashes:
            self.entries.pop(key_hash, None)

    async def delete_expired(self, cutoff: datetime, *, limit: int = 100) -> int:
        expired = [key for key, entry in self.entries.items() if entry.updated_at < cutoff][:limit]
        for key in expired:
            self.entries.pop(key)
        return len(expired)


def make_throttle(
    repository: FakeThrottleRepository,
    clock: FrozenClock,
) -> LoginThrottle:
    return LoginThrottle(
        repository=repository,
        clock=clock,
        policy=POLICY,
        pepper=b"test-login-throttle-pepper",
    )


@pytest.mark.asyncio
async def test_eighth_failure_blocks_without_storing_email_or_ip() -> None:
    repository = FakeThrottleRepository()
    throttle = make_throttle(repository, FrozenClock(NOW))

    for _ in range(7):
        assert await throttle.record_failure("user@example.com", "203.0.113.9") is False
    assert await throttle.record_failure("user@example.com", "203.0.113.9") is True
    assert await throttle.is_blocked("user@example.com", "203.0.113.9") is True

    assert len(repository.entries) == 2
    assert all(len(key) == 64 for key in repository.entries)
    assert "user@example.com" not in repr(repository.entries)
    assert "203.0.113.9" not in repr(repository.entries)


@pytest.mark.asyncio
async def test_failure_window_resets_after_fifteen_minutes() -> None:
    repository = FakeThrottleRepository()
    clock = FrozenClock(NOW)
    throttle = make_throttle(repository, clock)

    for _ in range(7):
        await throttle.record_failure("user@example.com", "203.0.113.9")
    clock.current = NOW + POLICY.window + timedelta(seconds=1)

    assert await throttle.record_failure("user@example.com", "203.0.113.9") is False
    assert {entry.failure_count for entry in repository.entries.values()} == {1}


@pytest.mark.asyncio
async def test_block_expires_and_success_clears_both_buckets() -> None:
    repository = FakeThrottleRepository()
    clock = FrozenClock(NOW)
    throttle = make_throttle(repository, clock)

    for _ in range(POLICY.max_failures):
        await throttle.record_failure("user@example.com", "203.0.113.9")
    clock.current = NOW + POLICY.blocked_for + timedelta(seconds=1)

    assert await throttle.is_blocked("user@example.com", "203.0.113.9") is False
    await throttle.clear_success("user@example.com", "203.0.113.9")
    assert repository.entries == {}
    assert len(repository.cleared[0]) == 2


def test_hmac_keys_are_deterministic_and_domain_separated() -> None:
    throttle = make_throttle(FakeThrottleRepository(), FrozenClock(NOW))

    account_key, address_key = throttle.key_hashes("USER@example.com", "203.0.113.9")
    expected = hmac.new(
        b"test-login-throttle-pepper",
        b"account\0user@example.com",
        sha256,
    ).hexdigest()

    assert account_key == expected
    assert address_key != account_key
    assert throttle.key_hashes("user@example.com", "203.0.113.9") == (
        account_key,
        address_key,
    )
    assert throttle.key_hashes("user@example.com", "203.0.113.10")[1] != address_key
