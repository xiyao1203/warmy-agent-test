"""TestAccount 领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class TestAccountId:
    value: UUID

    @classmethod
    def new(cls) -> TestAccountId:
        return cls(uuid4())


@dataclass(slots=True)
class TestAccount:
    """测试账号实体。

    存储项目测试账号信息，凭证字段加密存储。

    Attributes:
        account_id: 账号唯一标识。
        project_id: 所属项目 ID。
        name: 账号名称（如 admin、viewer）。
        username: 登录用户名。
        credential_encrypted: 加密存储的凭证（密码/token）。
        account_type: 账号类型（admin / user / readonly）。
        enabled: 是否启用。
        created_at: 创建时间。
        updated_at: 更新时间。
        description: 可选描述。
    """

    account_id: TestAccountId
    project_id: UUID
    name: str
    username: str
    credential_encrypted: str
    account_type: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    environment_template_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID,
        name: str,
        username: str,
        credential_encrypted: str,
        account_type: str = "user",
        description: str | None = None,
        environment_template_id: UUID | None = None,
    ) -> TestAccount:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Account name is required")
        if not username.strip():
            raise ValueError("Username is required")
        now = datetime.now(UTC)
        return cls(
            account_id=TestAccountId.new(),
            project_id=project_id,
            name=normalized_name,
            username=username.strip(),
            credential_encrypted=credential_encrypted,
            account_type=account_type,
            enabled=True,
            created_at=now,
            updated_at=now,
            description=description,
            environment_template_id=environment_template_id,
        )

    def update_credential(self, credential_encrypted: str) -> None:
        self.credential_encrypted = credential_encrypted
        self.updated_at = datetime.now(UTC)

    def toggle(self) -> None:
        self.enabled = not self.enabled
        self.updated_at = datetime.now(UTC)
