.PHONY: bootstrap format lint typecheck test build verify architecture api-generate api-check mission-acceptance

bootstrap:
	pnpm install --frozen-lockfile
	uv sync --all-packages

format:
	pnpm format
	uv run ruff format --check .

lint:
	pnpm lint
	uv run ruff check .

typecheck:
	pnpm typecheck
	uv run mypy apps/control-api/src apps/admin-cli/src

test:
	pnpm test
	uv run pytest

build:
	pnpm build

architecture:
	uv run pytest apps/control-api/tests/architecture -v
	uv run python scripts/check_architecture.py

verify: format lint typecheck test build architecture api-check

api-generate:
	uv run python scripts/export_openapi.py
	pnpm --filter @warmy/generated-api-client generate

api-check:
	$(MAKE) api-generate
	git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src/client

mission-acceptance:
	uv run python scripts/run_mission_acceptance.py
