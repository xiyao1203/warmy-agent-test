from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from secrets import token_urlsafe
from time import monotonic
from uuid import uuid4

import httpx
from agenttest.bootstrap.settings import Settings, get_settings
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyCredentialRepository,
    SqlAlchemyUserRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def unique_run_ids(assets: list[dict[str, object]]) -> list[str]:
    return sorted(
        {str(item["id"]) for item in assets if item.get("type") == "run" and item.get("id")}
    )


@dataclass(frozen=True, slots=True)
class AcceptanceIdentity:
    email: str
    password: str


async def create_acceptance_identity(settings: Settings) -> AcceptanceIdentity:
    identity = AcceptanceIdentity(
        email=f"mission-acceptance-{uuid4()}@example.test",
        password=token_urlsafe(32),
    )
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    try:
        user = User.create(
            user_id=UserId.new(),
            email=Email(identity.email),
            display_name="Mission Acceptance",
            role=SystemRole.SUPER_ADMIN,
        )
        await SqlAlchemyUserRepository(session_factory).add(user)
        await SqlAlchemyCredentialRepository(session_factory).set_password_hash(
            user.user_id, Argon2PasswordHasher().hash(identity.password)
        )
    finally:
        await engine.dispose()
    return identity


async def run_acceptance(*, control_api: str, target_url: str, timeout_seconds: float) -> None:
    settings = get_settings()
    identity = await create_acceptance_identity(settings)
    async with httpx.AsyncClient(base_url=control_api, timeout=20, trust_env=False) as client:
        health = await client.get("/api/v1/health")
        health.raise_for_status()
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": identity.email, "password": identity.password},
        )
        login.raise_for_status()
        csrf = client.cookies.get("agenttest_csrf")
        if not csrf:
            raise RuntimeError("Control API login did not issue a CSRF token")
        headers = {"X-CSRF-Token": csrf}
        project_response = await client.post(
            "/api/v1/projects",
            json={"name": f"Mission Acceptance {uuid4()}"},
            headers=headers,
        )
        project_response.raise_for_status()
        project_id = str(project_response.json()["id"])
        session_response = await client.post(
            f"/api/v1/projects/{project_id}/test-agent/sessions", headers=headers
        )
        session_response.raise_for_status()
        session_id = str(session_response.json()["session_id"])
        mission_response = await client.post(
            f"/api/v1/projects/{project_id}/test-missions",
            headers=headers,
            json={
                "session_id": session_id,
                "facts": {
                    "target_url": target_url,
                    "access_strategy": "none",
                    "test_goal": "Verify deterministic chat success",
                    "safety_scope": "read_only",
                    "scenario_hints": ["success", "security baseline"],
                },
            },
        )
        mission_response.raise_for_status()
        mission_id = str(mission_response.json()["mission_id"])
        discovery = await client.post(
            f"/api/v1/projects/{project_id}/test-missions/{mission_id}/discover",
            headers=headers,
        )
        discovery.raise_for_status()
        preview = await client.post(
            f"/api/v1/projects/{project_id}/test-missions/{mission_id}/preview",
            headers=headers,
        )
        preview.raise_for_status()
        preview_body = preview.json()
        if not preview_body["ready"]:
            raise RuntimeError(f"Mission preview is not ready: {preview_body['missing_inputs']}")
        confirm_body = {
            "revision_hash": preview_body["revision_hash"],
            "idempotency_key": f"acceptance-{mission_id}",
        }
        first = await client.post(
            f"/api/v1/projects/{project_id}/test-missions/{mission_id}/confirm-start",
            headers=headers,
            json=confirm_body,
        )
        first.raise_for_status()
        second = await client.post(
            f"/api/v1/projects/{project_id}/test-missions/{mission_id}/confirm-start",
            headers=headers,
            json=confirm_body,
        )
        second.raise_for_status()
        if first.json()["workflow_id"] != second.json()["workflow_id"]:
            raise RuntimeError("Duplicate confirmation created a second workflow")
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            status = await client.get(f"/api/v1/projects/{project_id}/test-missions/{mission_id}")
            status.raise_for_status()
            body = status.json()
            if body["status"] in {"completed", "failed", "cancelled", "needs_attention"}:
                run_ids = unique_run_ids(body.get("assets", []))
                if len(run_ids) != 1:
                    raise RuntimeError(f"Expected one Run, found {len(run_ids)}")
                print(f"Mission {mission_id} reached {body['status']} with Run {run_ids[0]}")
                if body["status"] != "completed":
                    raise RuntimeError(f"Acceptance mission ended as {body['status']}")
                return
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Mission {mission_id} did not finish within {timeout_seconds:g}s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-api", default="http://127.0.0.1:8181")
    parser.add_argument("--target-url", default="http://127.0.0.1:8199")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    asyncio.run(
        run_acceptance(
            control_api=args.control_api,
            target_url=args.target_url,
            timeout_seconds=args.timeout,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
