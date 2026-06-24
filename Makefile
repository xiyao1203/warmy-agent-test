.PHONY: bootstrap format lint typecheck test build verify

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
