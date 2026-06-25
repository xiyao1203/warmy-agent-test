from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

type UnitOfWorkFactory = Callable[[], AbstractAsyncContextManager[Any]]


class NullUnitOfWork:
    async def __aenter__(self) -> "NullUnitOfWork":
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


def null_uow_factory() -> AbstractAsyncContextManager[Any]:
    return NullUnitOfWork()
