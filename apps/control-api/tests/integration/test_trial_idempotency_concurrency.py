from __future__ import annotations

import json
import os
from asyncio import gather, to_thread
from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg
import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.modules.runs.public import RunIdempotencyKeyExists
from agenttest.modules.test_plans.public import TestPlanVersionId as PlanVersionId
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)
from alembic import command
from alembic.config import Config


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_postgresql_trial_key_race_has_one_winner_and_public_conflict() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config("apps/control-api/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.upgrade, config, "head")
    identifiers = await _seed_dependencies(database_url)
    engine = create_database_engine(database_url)
    repository = SqlAlchemyRunRepository(create_session_factory(engine))
    try:
        runs_and_cases = [_trial(identifiers, "concurrent-case-trial") for _ in range(2)]
        results = await gather(
            *(repository.add(run, [run_case]) for run, run_case in runs_and_cases),
            return_exceptions=True,
        )

        assert sum(result is None for result in results) == 1
        conflicts = [result for result in results if isinstance(result, RunIdempotencyKeyExists)]
        assert len(conflicts) == 1, results
        stored = await repository.get_by_idempotency_key(
            ProjectId(identifiers["project_id"]),
            "concurrent-case-trial",
        )
        assert stored is not None
        assert stored.source_test_case_id == identifiers["case_id"]
    finally:
        await engine.dispose()
        await _cleanup(database_url, identifiers)


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_postgresql_plan_key_race_recovers_winner_inside_route_uow() -> None:
    """A losing request can query the winner before its outer route UoW exits."""
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config("apps/control-api/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.upgrade, config, "head")
    identifiers = await _seed_dependencies(database_url)
    engine = create_database_engine(database_url)
    session_factory = create_session_factory(engine)
    repository = SqlAlchemyRunRepository(session_factory)

    async def create_or_recover(run: Run, run_case: RunCase) -> RunId:
        async with SqlAlchemyUnitOfWork(session_factory):
            try:
                await repository.add(run, [run_case])
            except RunIdempotencyKeyExists:
                winner = await repository.get_by_idempotency_key(
                    ProjectId(identifiers["project_id"]),
                    "concurrent-plan-run",
                )
                assert winner is not None
                return winner.run_id
            return run.run_id

    try:
        runs_and_cases = [_plan(identifiers, "concurrent-plan-run") for _ in range(2)]
        results = await gather(
            *(create_or_recover(run, run_case) for run, run_case in runs_and_cases),
        )

        assert results[0] == results[1]
        stored = await repository.get_by_idempotency_key(
            ProjectId(identifiers["project_id"]),
            "concurrent-plan-run",
        )
        assert stored is not None
        assert stored.run_id == results[0]
        assert stored.test_plan_version_id == PlanVersionId(identifiers["test_plan_version_id"])
    finally:
        await engine.dispose()
        await _cleanup(database_url, identifiers)


def _trial(identifiers: dict[str, UUID], key: str) -> tuple[Run, RunCase]:
    run = Run.create_case_trial(
        run_id=RunId.new(),
        project_id=ProjectId(identifiers["project_id"]),
        source_test_case_id=identifiers["case_id"],
        agent_version_id=identifiers["agent_version_id"],
        dataset_version_id=identifiers["dataset_version_id"],
        idempotency_key=key,
        created_by=UserId(identifiers["user_id"]),
        config_snapshot={"case_trial_request_fingerprint": "f" * 64},
        plugin_snapshot={"id": "generic-http"},
    )
    return run, RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=identifiers["case_id"],
        name="Concurrent trial",
        input_snapshot={"message": "hello"},
        assertion_snapshot=[{"type": "contains", "value": "hello"}],
        case_spec_snapshot={"schema_version": "platform-test-case/v1"},
    )


def _plan(identifiers: dict[str, UUID], key: str) -> tuple[Run, RunCase]:
    run = Run.create(
        run_id=RunId.new(),
        project_id=ProjectId(identifiers["project_id"]),
        test_plan_version_id=PlanVersionId(identifiers["test_plan_version_id"]),
        agent_version_id=identifiers["agent_version_id"],
        dataset_version_id=identifiers["dataset_version_id"],
        idempotency_key=key,
        created_by=UserId(identifiers["user_id"]),
        config_snapshot={"plan_run_request_fingerprint": "f" * 64},
        plugin_snapshot={"id": "generic-http"},
        total_cases=1,
    )
    return run, RunCase.create(
        run_case_id=RunCaseId.new(),
        run_id=run.run_id,
        test_case_id=identifiers["case_id"],
        name="Concurrent plan",
        input_snapshot={"message": "hello"},
        assertion_snapshot=[{"type": "contains", "value": "hello"}],
        case_spec_snapshot={"schema_version": "platform-test-case/v1"},
    )


async def _seed_dependencies(database_url: str) -> dict[str, UUID]:
    ids = {
        "user_id": uuid4(),
        "project_id": uuid4(),
        "agent_id": uuid4(),
        "agent_version_id": uuid4(),
        "dataset_id": uuid4(),
        "dataset_version_id": uuid4(),
        "case_id": uuid4(),
        "test_plan_id": uuid4(),
        "test_plan_version_id": uuid4(),
    }
    now = datetime.now(UTC)
    connection = await asyncpg.connect(_postgres_dsn(database_url))
    try:
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO users (
                    id, email, email_normalized, display_name, role, status,
                    must_change_password, created_at, updated_at
                ) VALUES ($1, $2, $2, 'Trial', 'tester', 'active', false, $3, $3)
                """,
                ids["user_id"],
                f"trial-{ids['user_id']}@example.test",
                now,
            )
            await connection.execute(
                """
                INSERT INTO projects (
                    id, key, name, created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, 'Trial race', $3, $3, $4, $4)
                """,
                ids["project_id"],
                f"T{ids['project_id'].hex[:8].upper()}",
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO agents (
                    id, project_id, name, agent_type, created_at, updated_at,
                    created_by, updated_by
                ) VALUES ($1, $2, 'Trial agent', 'generic_http', $3, $3, $4, $4)
                """,
                ids["agent_id"],
                ids["project_id"],
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO agent_versions (
                    id, agent_id, version_number, status, config, schema_version,
                    readiness_status, created_at, updated_at, created_by
                ) VALUES ($1, $2, 1, 'published', $3, 1, 'ready', $4, $4, $5)
                """,
                ids["agent_version_id"],
                ids["agent_id"],
                json.dumps({"endpoint_url": "https://agent.test"}),
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO datasets (
                    id, project_id, name, created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, 'Trial data', $3, $3, $4, $4)
                """,
                ids["dataset_id"],
                ids["project_id"],
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO dataset_versions (
                    id, dataset_id, version_number, status, created_at, updated_at, created_by
                ) VALUES ($1, $2, 1, 'draft', $3, $3, $4)
                """,
                ids["dataset_version_id"],
                ids["dataset_id"],
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO test_cases (
                    id, dataset_version_id, case_key, name, objective, case_status,
                    template, case_type, automation_status, source, requirement_refs,
                    input, preconditions, data_bindings, steps, execution_mode,
                    assertions, scorers, security_policies, artifact_requirements,
                    postconditions, retry_count, custom_fields, tags, sort_order,
                    created_by, updated_by, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, 'Concurrent trial', 'Verify idempotency', 'ready',
                    'ai_eval', 'functional', 'automated', 'manual', $4,
                    $5, $4, $4, $4, 'api', $6, $4, $4, $4, $4, 0, $5, $4, 1,
                    $7, $7, $8, $8
                )
                """,
                ids["case_id"],
                ids["dataset_version_id"],
                f"T-{ids['case_id'].hex[:12].upper()}",
                json.dumps([]),
                json.dumps({"message": "hello"}),
                json.dumps([{"type": "contains", "value": "hello"}]),
                ids["user_id"],
                now,
            )
            await connection.execute(
                """
                INSERT INTO test_plans (
                    id, project_id, name, created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, 'Concurrent plan', $3, $3, $4, $4)
                """,
                ids["test_plan_id"],
                ids["project_id"],
                now,
                ids["user_id"],
            )
            await connection.execute(
                """
                INSERT INTO test_plan_versions (
                    id, test_plan_id, version_number, status, agent_version_id,
                    dataset_version_id, config, created_at, updated_at, created_by
                ) VALUES ($1, $2, 1, 'published', $3, $4, $5, $6, $6, $7)
                """,
                ids["test_plan_version_id"],
                ids["test_plan_id"],
                ids["agent_version_id"],
                ids["dataset_version_id"],
                json.dumps({}),
                now,
                ids["user_id"],
            )
    finally:
        await connection.close()
    return ids


async def _cleanup(database_url: str, identifiers: dict[str, UUID]) -> None:
    connection = await asyncpg.connect(_postgres_dsn(database_url))
    try:
        await connection.execute("DELETE FROM projects WHERE id = $1", identifiers["project_id"])
        await connection.execute("DELETE FROM users WHERE id = $1", identifiers["user_id"])
    finally:
        await connection.close()


def _postgres_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")
