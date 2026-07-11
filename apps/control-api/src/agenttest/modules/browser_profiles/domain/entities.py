from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class BrowserProfile:
    id: UUID
    project_id: UUID
    name: str
    target_domain: str
    status: str
    auth_state_status: str
    auth_state_envelope: str | None
    auth_state_sha256: str | None
    auth_state_version: int
    auth_state_updated_at: datetime | None
    last_login_at: datetime | None
    last_verified_at: datetime | None
    user_data_dir: str
    cdp_port: int | None
    cdp_endpoint: str
    locked_by_run_case_id: UUID | None
    locked_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        name: str,
        target_domain: str,
        created_by: UUID,
        now: datetime,
    ) -> BrowserProfile:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("浏览器实例名称不能为空")
        return cls(
            id=uuid4(),
            project_id=project_id,
            name=normalized_name,
            target_domain=target_domain.strip(),
            status="stopped",
            auth_state_status="missing",
            auth_state_envelope=None,
            auth_state_sha256=None,
            auth_state_version=0,
            auth_state_updated_at=None,
            last_login_at=None,
            last_verified_at=None,
            user_data_dir="",
            cdp_port=None,
            cdp_endpoint="",
            locked_by_run_case_id=None,
            locked_at=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    def store_auth_state(self, *, envelope: str, sha256: str, saved_at: datetime) -> None:
        if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
            raise ValueError("登录态 SHA-256 无效")
        if not envelope:
            raise ValueError("加密登录态不能为空")
        self.auth_state_envelope = envelope
        self.auth_state_sha256 = sha256
        self.auth_state_version += 1
        self.auth_state_updated_at = saved_at
        self.last_login_at = saved_at
        self.updated_at = saved_at
        self.auth_state_status = "ready"

    def mark_auth_ready(self, verified_at: datetime) -> None:
        if not self.auth_state_envelope or not self.auth_state_sha256:
            raise ValueError("缺少可验证的登录态快照")
        self.auth_state_status = "ready"
        self.last_verified_at = verified_at
        self.updated_at = verified_at

    def to_public_dict(self) -> dict[str, object]:
        return {
            "profile_id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "target_domain": self.target_domain,
            "status": self.status,
            "auth_state_status": self.auth_state_status,
            "auth_state_version": self.auth_state_version,
            "auth_state_updated_at": (
                self.auth_state_updated_at.isoformat() if self.auth_state_updated_at else None
            ),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_verified_at": (
                self.last_verified_at.isoformat() if self.last_verified_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
