from __future__ import annotations

from typing import Any

import pytest
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    current_database_session,
)


class FakeTransaction:
    def __init__(self) -> None:
        self.entered = False
        self.exited_with: tuple[Any, Any, Any] | None = None

    async def __aenter__(self) -> None:
        self.entered = True

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.exited_with = (exc_type, exc, traceback)


class FakeSession:
    def __init__(self) -> None:
        self.transaction = FakeTransaction()
        self.closed = False

    def begin(self) -> FakeTransaction:
        return self.transaction

    async def close(self) -> None:
        self.closed = True


class FakeFactory:
    def __init__(self) -> None:
        self.session = FakeSession()

    def __call__(self) -> FakeSession:
        return self.session


@pytest.mark.asyncio
async def test_unit_of_work_exposes_one_shared_session_and_closes_it() -> None:
    factory = FakeFactory()

    async with SqlAlchemyUnitOfWork(factory):  # type: ignore[arg-type]
        assert current_database_session() is factory.session

    assert current_database_session() is None
    assert factory.session.transaction.entered is True
    assert factory.session.transaction.exited_with == (None, None, None)
    assert factory.session.closed is True


@pytest.mark.asyncio
async def test_unit_of_work_passes_exception_to_transaction_for_rollback() -> None:
    factory = FakeFactory()

    with pytest.raises(RuntimeError):
        async with SqlAlchemyUnitOfWork(factory):  # type: ignore[arg-type]
            raise RuntimeError("business failure")

    assert factory.session.transaction.exited_with is not None
    assert factory.session.transaction.exited_with[0] is RuntimeError
