# Fake Agent Target

Deterministic production-isomorphic target for AgentTest acceptance tests. Start it with:

```bash
uv run uvicorn tests.fake_agent_target.app:app --port 8199
```

Configure a scenario through `POST /control/scenario`, invoke the API through
`POST /api/agent/invoke`, and inspect observable calls through
`GET /control/observations`. All leak/security payloads use synthetic markers.
