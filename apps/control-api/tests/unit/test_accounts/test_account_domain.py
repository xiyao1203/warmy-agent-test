"""Unit tests for TestAccount domain entity."""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.test_accounts.domain.entities import (
    TestAccount,
)


def test_account_create() -> None:
    a = TestAccount.create(
        project_id=uuid4(),
        name="Admin Account",
        username="admin",
        credential_encrypted="encrypted_password",
        account_type="admin",
    )
    assert a.name == "Admin Account"
    assert a.username == "admin"
    assert a.account_type == "admin"
    assert a.enabled is True


def test_account_requires_name() -> None:
    with pytest.raises(ValueError, match="Account name is required"):
        TestAccount.create(
            project_id=uuid4(),
            name="  ",
            username="admin",
            credential_encrypted="pwd",
        )


def test_account_requires_username() -> None:
    with pytest.raises(ValueError, match="Username is required"):
        TestAccount.create(
            project_id=uuid4(),
            name="Admin",
            username="  ",
            credential_encrypted="pwd",
        )


def test_account_update_credential() -> None:
    a = TestAccount.create(
        project_id=uuid4(),
        name="Test",
        username="user",
        credential_encrypted="old_encrypted",
    )
    a.update_credential("new_encrypted")
    assert a.credential_encrypted == "new_encrypted"


def test_account_toggle() -> None:
    a = TestAccount.create(
        project_id=uuid4(),
        name="Test",
        username="user",
        credential_encrypted="pwd",
    )
    assert a.enabled is True
    a.toggle()
    assert a.enabled is False
    a.toggle()
    assert a.enabled is True
