.PHONY: bootstrap format lint typecheck test build verify api-generate api-check

bootstrap:
	pnpm install --frozen-lockfile
	uv sync --all-packages

format:
	pnpm format
	uv run ruff format .

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

verify: format lint typecheck test build

api-generate:
	uv run python scripts/export_openapi.py
	pnpm --filter @warmy/generated-api-client generate

api-check:
	$(MAKE) api-generate
	git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src
