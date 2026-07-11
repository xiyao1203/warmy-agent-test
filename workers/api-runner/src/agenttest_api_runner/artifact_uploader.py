"""Upload large run evidence to the control plane without embedding it in Temporal."""

from __future__ import annotations

import hashlib

import httpx


class ArtifactUploader:
    def __init__(
        self,
        base_url: str,
        internal_token: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_token = internal_token
        self._client = client

    async def upload(
        self,
        *,
        project_id: str,
        run_id: str,
        run_case_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> dict[str, object]:
        client = self._client or httpx.AsyncClient(timeout=30, trust_env=False)
        close = self._client is None
        digest = hashlib.sha256(content).hexdigest()
        try:
            response = await client.post(
                f"{self._base_url}/api/v1/internal/projects/{project_id}/runs/{run_id}/artifacts",
                headers={"X-Internal-Token": self._internal_token},
                data={"run_case_id": run_case_id, "sha256": digest},
                files={"file": (filename, content, content_type)},
            )
            response.raise_for_status()
            descriptor = dict(response.json())
            descriptor["sha256"] = digest
            descriptor["run_case_id"] = run_case_id
            return descriptor
        finally:
            if close:
                await client.aclose()
