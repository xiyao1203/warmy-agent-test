from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
    BrowserAuthStateCipher,
)


@dataclass(frozen=True, slots=True)
class AuthStateSnapshot:
    envelope: str
    sha256: str


class BrowserAuthStateService:
    def __init__(self, cipher: BrowserAuthStateCipher) -> None:
        self._cipher = cipher

    def seal(
        self,
        *,
        project_id: UUID,
        profile_id: UUID,
        target_domain: str,
        storage_state: dict[str, Any],
    ) -> AuthStateSnapshot:
        target_host = _host(target_domain)
        if not target_host or not _has_target_state(storage_state, target_host):
            raise ValueError("登录态不包含目标域的 Cookie、LocalStorage 或 IndexedDB")
        canonical = json.dumps(
            storage_state,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return AuthStateSnapshot(
            envelope=self._cipher.encrypt(project_id, profile_id, canonical),
            sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )

    def open(self, project_id: UUID, profile_id: UUID, envelope: str) -> dict[str, Any]:
        plaintext = self._cipher.decrypt(project_id, profile_id, envelope)
        try:
            value = json.loads(plaintext)
        except json.JSONDecodeError as error:
            raise ValueError("浏览器登录态格式无效") from error
        if not isinstance(value, dict):
            raise ValueError("浏览器登录态格式必须是对象")
        return value


def _host(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return (parsed.hostname or "").rstrip(".")


def _domain_matches(target_host: str, state_host: str) -> bool:
    normalized = state_host.strip().lower().lstrip(".").rstrip(".")
    return bool(normalized) and (
        target_host == normalized or target_host.endswith(f".{normalized}")
    )


def _has_target_state(storage_state: dict[str, Any], target_host: str) -> bool:
    cookies = storage_state.get("cookies")
    if isinstance(cookies, list):
        for cookie in cookies:
            if (
                isinstance(cookie, dict)
                and cookie.get("name")
                and _domain_matches(target_host, str(cookie.get("domain") or ""))
            ):
                return True
    origins = storage_state.get("origins")
    if isinstance(origins, list):
        for origin in origins:
            if not isinstance(origin, dict):
                continue
            origin_host = _host(str(origin.get("origin") or ""))
            if not _domain_matches(target_host, origin_host):
                continue
            local_storage = origin.get("localStorage")
            indexed_db = origin.get("indexedDB")
            if (isinstance(local_storage, list) and local_storage) or (
                isinstance(indexed_db, list) and indexed_db
            ):
                return True
    return False
