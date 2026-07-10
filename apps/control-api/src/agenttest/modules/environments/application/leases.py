"""Short-lived, project-scoped credential redemption."""

from __future__ import annotations

from uuid import UUID

from agenttest.modules.environments.application.credentials import (
    CredentialCipher,
    CredentialRepository,
)


class CredentialLeaseService:
    def __init__(self, repository: CredentialRepository, cipher: CredentialCipher) -> None:
        self._repository = repository
        self._cipher = cipher

    async def redeem(
        self,
        project_id: UUID,
        credential_ids: list[UUID],
    ) -> dict[str, str]:
        records = await self._repository.get_many(project_id, credential_ids)
        if len(records) != len(set(credential_ids)):
            raise PermissionError("credential binding is outside the project")
        return {
            record.injection_name: self._cipher.decrypt(record.encrypted_value)
            for record in records
        }
