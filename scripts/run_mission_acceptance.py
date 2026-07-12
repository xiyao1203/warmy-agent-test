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

TRUST_LOOP_SCENARIOS = (
    "success",
    "product_error",
    "protocol_error",
    "auth_expired",
    "quota_exceeded",
    "timeout",
    "transient_failure",
    "incomplete_artifact",
    "prompt_injection",
)


def validate_trust_loop_payload(
    *,
    scenario: str,
    run: dict[str, object],
    cases: dict[str, object],
    summary: dict[str, object],
    diagnostics: dict[str, object],
    regressions: dict[str, object],
    calibration: dict[str, object],
    gate: dict[str, object],
) -> None:
    assert summary.get("job_id"), "trust loop must expose one durable job"
    assert summary.get("run_id") == run.get("id"), "trust loop Run scope mismatch"
    assert summary.get("status") in {
        "completed",
        "completed_with_warnings",
        "failed",
    }, "trust loop did not reach a terminal state"
    serialized = repr((summary, diagnostics, regressions, calibration, gate)).lower()
    assert "api key" not in serialized and "provider error" not in serialized

    expected_classes = {
        "product_error": "target_failure",
        "protocol_error": "target_failure",
        "auth_expired": "environment_failure",
        "quota_exceeded": "environment_failure",
        "timeout": "environment_failure",
    }
    raw_classifications = summary.get("classifications")
    classifications = raw_classifications if isinstance(raw_classifications, list) else []
    expected = expected_classes.get(scenario)
    if expected:
        actual = {
            str(item.get("failure_class")) for item in classifications if isinstance(item, dict)
        }
        assert expected in actual, f"{scenario} did not produce {expected}"

    assert isinstance(diagnostics.get("items"), list)
    assert calibration.get("status") in {"completed", "inconclusive"}
    assert gate.get("status") == "completed"
    assert gate.get("decision") in {"allow", "block", "needs_review", "quarantine"}
    if scenario in {"incomplete_artifact", "prompt_injection"}:
        assert gate.get("decision") == "block", f"{scenario} must fail closed"

    raw_candidates = regressions.get("items")
    candidates = raw_candidates if isinstance(raw_candidates, list) else []
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("status") != "published":
            continue
        assert int(candidate.get("reproduction_count") or 0) >= 2, (
            "published regression requires two independent reproductions"
        )
    if scenario in {"product_error", "protocol_error"}:
        assert candidates, f"{scenario} must produce a regression candidate"
        assert all(candidate.get("status") != "published" for candidate in candidates), (
            "unreproduced candidates must remain quarantined"
        )

    raw_cases = cases.get("items")
    case_items = raw_cases if isinstance(raw_cases, list) else []
    if scenario == "transient_failure":
        recovered = any(
            item.get("status") == "passed" for item in case_items if isinstance(item, dict)
        )
        assert recovered, "transient failure did not recover through Temporal retry"
    if scenario == "prompt_injection":
        assert any(
            isinstance(item, dict)
            and isinstance(item.get("security_summary"), dict)
            and item["security_summary"].get("decision") == "blocked"
            for item in case_items
        ), "security signal was not persisted as blocked"


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


async def run_acceptance(
    *, control_api: str, target_url: str, timeout_seconds: float, scenario: str = "success"
) -> None:
    if scenario not in TRUST_LOOP_SCENARIOS:
        raise ValueError(f"Unsupported trust-loop scenario: {scenario}")
    async with httpx.AsyncClient(base_url=target_url, timeout=10, trust_env=False) as target:
        configured = await target.post(
            "/control/scenario",
            json={
                "name": scenario,
                "failures": 1 if scenario == "transient_failure" else 0,
                "delay_seconds": 0,
            },
        )
        configured.raise_for_status()
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
                    "test_goal": f"Verify deterministic {scenario} handling",
                    "safety_scope": "read_only",
                    "scenario_hints": [scenario, "security baseline"],
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
                expected_status = "needs_attention" if scenario == "auth_expired" else "completed"
                print(
                    f"Mission {mission_id} reached {body['status']} with Run {run_ids[0]} "
                    f"for {scenario}"
                )
                if body["status"] != expected_status:
                    raise RuntimeError(f"Acceptance mission ended as {body['status']}")
                run_id = run_ids[0]
                break
            await asyncio.sleep(0.5)
        else:
            raise TimeoutError(f"Mission {mission_id} did not finish within {timeout_seconds:g}s")

        deadline = monotonic() + timeout_seconds
        trust_url = f"/api/v1/projects/{project_id}/runs/{run_id}/trust-loop"
        while monotonic() < deadline:
            trust = await client.get(trust_url)
            trust.raise_for_status()
            summary = trust.json()
            if summary["status"] in {"completed", "completed_with_warnings", "failed"}:
                break
            await asyncio.sleep(0.5)
        else:
            raise TimeoutError(f"Run {run_id} trust loop did not finish")

        endpoints = {
            "run": f"/api/v1/projects/{project_id}/runs/{run_id}",
            "cases": f"/api/v1/projects/{project_id}/runs/{run_id}/cases",
            "diagnostics": f"/api/v1/projects/{project_id}/runs/{run_id}/diagnostics",
            "regressions": f"/api/v1/projects/{project_id}/runs/{run_id}/regressions",
            "calibration": f"/api/v1/projects/{project_id}/runs/{run_id}/calibration",
            "gate": f"/api/v1/projects/{project_id}/runs/{run_id}/joint-gate",
        }
        payloads: dict[str, dict[str, object]] = {}
        for name, url in endpoints.items():
            response = await client.get(url)
            response.raise_for_status()
            payloads[name] = response.json()
        validate_trust_loop_payload(
            scenario=scenario,
            run=payloads["run"],
            cases=payloads["cases"],
            summary=summary,
            diagnostics=payloads["diagnostics"],
            regressions=payloads["regressions"],
            calibration=payloads["calibration"],
            gate=payloads["gate"],
        )
        print(f"Trust loop {summary['job_id']} verified for {scenario}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--control-api", default="http://127.0.0.1:8181")
    parser.add_argument("--target-url", default="http://127.0.0.1:8199")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--scenario", choices=TRUST_LOOP_SCENARIOS, default="success")
    parser.add_argument("--matrix", action="store_true")
    args = parser.parse_args()
    scenarios = TRUST_LOOP_SCENARIOS if args.matrix else (args.scenario,)
    for scenario in scenarios:
        asyncio.run(
            run_acceptance(
                control_api=args.control_api,
                target_url=args.target_url,
                timeout_seconds=args.timeout,
                scenario=scenario,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
