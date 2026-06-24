# Local Development

## Prerequisites

- Docker with the Compose plugin
- Node.js and pnpm
- Python 3.12 or 3.13
- uv

## Start infrastructure

```bash
cp infra/compose/.env.example infra/compose/.env
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
```

Services:

| Service | Address |
|---|---|
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| Temporal | `localhost:7233` |
| Temporal UI | `http://localhost:8080` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |

The values in `.env.example` are local-only defaults. Do not reuse them in shared or
production environments.

## Stop infrastructure

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down
```

To remove local data as well:

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down --volumes
```
