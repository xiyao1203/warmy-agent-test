from __future__ import annotations

from base64 import urlsafe_b64decode
from binascii import Error as Base64Error

import httpx
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"agenttest:model-credential:v1"


class CredentialLeaseClient:
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
        binding_ids: list[str],
    ) -> dict[str, str]:
        client = self._client or httpx.AsyncClient(timeout=15)
        close = self._client is None
        try:
            response = await client.post(
                f"{self._base_url}/api/v1/internal/projects/{project_id}/credential-leases:redeem",
                headers={"X-Internal-Token": self._internal_token},
                json={
                    "run_id": run_id,
                    "run_case_id": run_case_id,
                    "binding_ids": binding_ids,
                },
            )
            response.raise_for_status()
            payload = response.json()
            values = payload.get("values", {})
            if not isinstance(values, dict):
                raise ValueError("credential lease response is invalid")
            return {str(key): str(value) for key, value in values.items()}
        finally:
            if close:
                await client.aclose()


def decrypt_credential(envelope: str, encoded_master_key: str) -> str:
    try:
        key = urlsafe_b64decode(encoded_master_key.encode())
        if len(key) != 32:
            raise ValueError
        version, encoded = envelope.split(".", 1)
        if version != "v1":
            raise ValueError
        encoded += "=" * (-len(encoded) % 4)
        payload = urlsafe_b64decode(encoded.encode())
        nonce, encrypted = payload[:12], payload[12:]
        if len(nonce) != 12 or not encrypted:
            raise ValueError
        return AESGCM(key).decrypt(nonce, encrypted, AAD).decode()
    except (ValueError, Base64Error, InvalidTag, UnicodeDecodeError) as error:
        raise ValueError("Credential decryption failed") from error
