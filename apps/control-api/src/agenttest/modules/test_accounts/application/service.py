from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_accounts.domain.entities import TestAccount, TestAccountId


class TestAccountRepository(Protocol):
    async def get_by_id_and_project(
        self, account_id: TestAccountId, project_id: UUID
    ) -> TestAccount | None: ...

    async def list_by_project(self, project_id: UUID, *, limit: int = 50) -> list[TestAccount]: ...

    async def add(self, account: TestAccount) -> None: ...

    async def save(self, account: TestAccount) -> None: ...

    async def delete(self, account_id: TestAccountId) -> None: ...


class ProjectAccessPort(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class TestAccountNotFound(Exception):
    pass


class TestAccountValidationError(Exception):
    pass


class TestAccountService:
    def __init__(
        self, *, accounts: TestAccountRepository, project_access: ProjectAccessPort
    ) -> None:
        self._accounts = accounts
        self._project_access = project_access

    async def list(self, actor: User, project_id: UUID) -> list[TestAccount]:
        await self._project_access.ensure_member(actor, ProjectId(project_id))
        return await self._accounts.list_by_project(project_id)

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        username: str,
        credential_encrypted: str,
        account_type: str,
        description: str | None,
    ) -> TestAccount:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        try:
            account = TestAccount.create(
                project_id=project_id,
                name=name,
                username=username,
                credential_encrypted=credential_encrypted,
                account_type=account_type,
                description=description,
            )
        except ValueError as error:
            raise TestAccountValidationError(str(error)) from error
        await self._accounts.add(account)
        return account

    async def update(
        self,
        actor: User,
        project_id: UUID,
        account_id: UUID,
        *,
        credential_encrypted: str | None,
        enabled: bool | None,
    ) -> TestAccount:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        account = await self._account(project_id, account_id)
        if credential_encrypted is not None:
            account.update_credential(credential_encrypted)
        if enabled is not None and enabled != account.enabled:
            account.toggle()
        await self._accounts.save(account)
        return account

    async def delete(self, actor: User, project_id: UUID, account_id: UUID) -> None:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        await self._account(project_id, account_id)
        await self._accounts.delete(TestAccountId(account_id))

    async def _account(self, project_id: UUID, account_id: UUID) -> TestAccount:
        account = await self._accounts.get_by_id_and_project(TestAccountId(account_id), project_id)
        if account is None:
            raise TestAccountNotFound
        return account
