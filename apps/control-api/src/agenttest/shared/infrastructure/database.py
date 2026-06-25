from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_current_session: ContextVar[AsyncSession | None] = ContextVar(
    "agenttest_database_session",
    default=None,
)


def create_database_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def current_database_session() -> AsyncSession | None:
    return _current_session.get()


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    current = current_database_session()
    if current is not None:
        yield current
        return
    async with session_factory() as session:
        yield session


@asynccontextmanager
async def transaction_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    current = current_database_session()
    if current is not None:
        yield current
        return
    async with SqlAlchemyUnitOfWork(session_factory):
        session = current_database_session()
        if session is None:
            raise RuntimeError("Unit of work did not create a database session")
        yield session


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._transaction: Any = None
        self._token: Token[AsyncSession | None] | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if current_database_session() is not None:
            return self
        self._session = self._session_factory()
        self._transaction = self._session.begin()
        await self._transaction.__aenter__()
        self._token = _current_session.set(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None or self._token is None:
            return
        try:
            await self._transaction.__aexit__(exc_type, exc, traceback)
        finally:
            _current_session.reset(self._token)
            await self._session.close()
