from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from agenttest.bootstrap.core_summaries import SqlAlchemyCoreSummaryReader
from agenttest.shared.application.core_summaries import CoreSummaryReader


class FailIfOpenedSessionFactory:
    def __call__(self) -> None:
        raise AssertionError("empty identifier lists must not open a database session")


def protocol_methods() -> set[str]:
    return {
        name
        for name, value in CoreSummaryReader.__dict__.items()
        if not name.startswith("_") and callable(value)
    }


def test_core_summary_facade_keeps_public_methods() -> None:
    assert protocol_methods() <= set(SqlAlchemyCoreSummaryReader.__dict__)


def test_core_summary_facade_delegates_to_separate_query_groups() -> None:
    reader = SqlAlchemyCoreSummaryReader(cast(Any, FailIfOpenedSessionFactory()))

    assert reader._assets.__class__.__module__.endswith(".assets")
    assert reader._execution.__class__.__module__.endswith(".execution")
    assert reader._quality.__class__.__module__.endswith(".quality")


@pytest.mark.asyncio
async def test_summary_reader_skips_database_for_empty_ids() -> None:
    reader = SqlAlchemyCoreSummaryReader(cast(Any, FailIfOpenedSessionFactory()))
    project_id = uuid4()

    calls = [reader.projects([])]
    for method_name in protocol_methods() - {"projects"}:
        method = cast(Any, getattr(reader, method_name))
        calls.append(method(project_id, []))

    assert all(awaitable is not None for awaitable in calls)
    results: list[dict[UUID, object]] = []
    for awaitable in calls:
        results.append(await awaitable)
    assert all(result == {} for result in results)
