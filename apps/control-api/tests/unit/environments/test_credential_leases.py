from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.environments.application.credentials import CredentialBindingRecord
from agenttest.modules.environments.application.leases import CredentialLeaseService


class Repository:
    def __init__(self, record: CredentialBindingRecord) -> None:
        self.record = record

    async def get_many(self, project_id, credential_ids):
        if project_id != self.record.project_id or self.record.id not in credential_ids:
            return []
        return [self.record]


class Cipher:
    def decrypt(self, envelope: str) -> str:
        assert envelope == "encrypted"
        return "real-password"


@pytest.mark.asyncio
async def test_redeem_is_project_scoped_and_uses_injection_names() -> None:
    project_id = uuid4()
    credential_id = uuid4()
    now = datetime.now(UTC)
    record = CredentialBindingRecord(
        id=credential_id,
        project_id=project_id,
        alias="TapNow password",
        kind="custom",
        injection_location="browser",
        injection_name="password",
        encrypted_value="encrypted",
        masked_hint="••••word",
        created_by=uuid4(),
        created_at=now,
        updated_at=now,
    )
    service = CredentialLeaseService(Repository(record), Cipher())

    assert await service.redeem(project_id, [credential_id]) == {"password": "real-password"}

    with pytest.raises(PermissionError, match="project"):
        await service.redeem(uuid4(), [credential_id])
