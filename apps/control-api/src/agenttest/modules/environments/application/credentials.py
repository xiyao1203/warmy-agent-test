from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from agenttest.modules.identity.public import User


@dataclass(frozen=True, slots=True)
class CredentialBindingRecord:
    id: UUID
    project_id: UUID
    alias: str
    kind: str
    injection_location: str
    injection_name: str
    encrypted_value: str
    masked_hint: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class CredentialRepository(Protocol):
    async def list(self, project_id: UUID) -> list[CredentialBindingRecord]: ...
    async def get_many(
        self, project_id: UUID, credential_ids: list[UUID]
    ) -> list[CredentialBindingRecord]: ...
    async def add(self, item: CredentialBindingRecord) -> None: ...
    async def delete(self, project_id: UUID, credential_id: UUID) -> bool: ...


class CredentialCipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...
    def decrypt(self, envelope: str) -> str: ...


class CredentialBindingService:
    def __init__(
        self,
        repository: CredentialRepository,
        cipher: CredentialCipher | None,
    ) -> None:
        self._repository = repository
        self._cipher = cipher

    async def list(self, project_id: UUID) -> list[CredentialBindingRecord]:
        return await self._repository.list(project_id)

    async def create(
        self,
        *,
        actor: User,
        project_id: UUID,
        alias: str,
        kind: str,
        injection_location: str,
        injection_name: str,
        value: str,
        now: datetime,
    ) -> CredentialBindingRecord:
        if self._cipher is None:
            raise RuntimeError("服务端未配置凭证加密密钥，无法安全保存凭证")
        item = CredentialBindingRecord(
            id=uuid4(),
            project_id=project_id,
            alias=alias.strip(),
            kind=kind,
            injection_location=injection_location,
            injection_name=injection_name.strip(),
            encrypted_value=self._cipher.encrypt(value),
            masked_hint=f"••••{value[-4:]}" if len(value) >= 4 else "••••",
            created_by=actor.user_id.value,
            created_at=now,
            updated_at=now,
        )
        await self._repository.add(item)
        return item

    async def delete(self, project_id: UUID, credential_id: UUID) -> bool:
        return await self._repository.delete(project_id, credential_id)
