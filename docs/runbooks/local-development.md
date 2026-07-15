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

## Security-sensitive Control API settings

Non-local deployments must provide an independent `AGENTTEST_LOGIN_THROTTLE_PEPPER`
and keep `AGENTTEST_TRUSTED_PROXY_CIDRS` empty unless requests always arrive through
known reverse-proxy networks. Only a directly connected peer in that allowlist may
supply `X-Forwarded-For`; never add public client ranges.

Artifact uploads default to 64 MiB for users and 256 MiB for internal Workers. Override
`AGENTTEST_ARTIFACT_USER_UPLOAD_MAX_BYTES` or
`AGENTTEST_ARTIFACT_INTERNAL_UPLOAD_MAX_BYTES` only after confirming object-store,
proxy, memory, and request-timeout budgets.

## Repository gates

```bash
make verify
make performance
make security-audit
```

Authenticated navigation sampling additionally requires running services and the E2E
admin/project environment variables before `make performance-e2e`.

## Stop infrastructure

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down
```

To remove local data as well:

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down --volumes
```
