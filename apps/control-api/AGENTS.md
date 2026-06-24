# Control API Instructions

Read the repository root `AGENTS.md` first.

## Commands

```bash
uv run pytest apps/control-api/tests
uv run ruff check apps/control-api
uv run mypy apps/control-api/src
```

## Boundaries

- Domain imports no FastAPI, SQLAlchemy, Redis, Temporal, Pydantic or vendor SDKs.
- Application defines use cases and ports.
- Infrastructure implements ports.
- API routes translate HTTP and never access ORM models directly.
- Cross-module imports use the target module's `public.py`.
- Every project-scoped repository method receives `project_id`.

## Database

- All schema changes use Alembic.
- Published migration files are immutable.
- Run empty-database and previous-revision migration tests.
