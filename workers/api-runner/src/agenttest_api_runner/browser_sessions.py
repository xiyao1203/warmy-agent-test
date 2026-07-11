from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class BrowserSessionLease:
    storage_state: dict
    auth_state_version: int


class BrowserSessionLeaseClient:
    def __init__(
        self,
        base_url: str,
        internal_token: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_token = internal_token
        self._client = client

    async def redeem(
        self,
        *,
        project_id: str,
        run_id: str,
        run_case_id: str,
        browser_profile_id: str,
    ) -> BrowserSessionLease:
        client = self._client or httpx.AsyncClient(timeout=15, trust_env=False)
        close = self._client is None
        try:
            response = await client.post(
                f"{self._base_url}/api/v1/internal/projects/{project_id}/browser-session-leases:redeem",
                headers={"X-Internal-Token": self._internal_token},
                json={
                    "run_id": run_id,
                    "run_case_id": run_case_id,
                    "browser_profile_id": browser_profile_id,
                },
            )
            if response.is_error:
                try:
                    detail = str(response.json().get("detail") or "browser session unavailable")
                except Exception:
                    detail = "browser session unavailable"
                raise RuntimeError(detail)
            payload = response.json()
            storage_state = payload.get("storage_state")
            version = payload.get("auth_state_version")
            if not isinstance(storage_state, dict) or not isinstance(version, int):
                raise RuntimeError("browser session lease response is invalid")
            return BrowserSessionLease(storage_state, version)
        finally:
            if close:
                await client.aclose()
