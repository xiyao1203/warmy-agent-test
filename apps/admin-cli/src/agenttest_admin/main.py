from __future__ import annotations

import argparse
import asyncio
import getpass
import os
from typing import Protocol

from agenttest.bootstrap.settings import get_settings
from agenttest.modules.identity.application.errors import DuplicateEmailError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyCredentialRepository,
    SqlAlchemyUserRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


class BootstrapUserRepository(Protocol):
    async def get_by_email(self, email: Email) -> User | None: ...

    async def add(self, user: User) -> None: ...


class BootstrapCredentialWriter(Protocol):
    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None: ...


async def create_super_admin(
    *,
    users: BootstrapUserRepository,
    credentials: BootstrapCredentialWriter,
    email: str,
    name: str,
    password: str,
) -> User:
    normalized_email = Email(email)
    if await users.get_by_email(normalized_email) is not None:
        raise DuplicateEmailError
    user = User.create(
        user_id=UserId.new(),
        email=normalized_email,
        display_name=name,
        role=SystemRole.SUPER_ADMIN,
    )
    user.require_password_change()
    await users.add(user)
    await credentials.set_password_hash(
        user.user_id,
        Argon2PasswordHasher().hash(password),
    )
    return user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agenttest-admin")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-super-admin")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    return parser


async def run_create_super_admin(email: str, name: str) -> int:
    password = os.environ.get("AGENTTEST_ADMIN_PASSWORD") or getpass.getpass("Initial password: ")
    if not password:
        raise ValueError("Initial password is required")
    settings = get_settings()
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    try:
        user = await create_super_admin(
            users=SqlAlchemyUserRepository(session_factory),
            credentials=SqlAlchemyCredentialRepository(session_factory),
            email=email,
            name=name,
            password=password,
        )
    finally:
        await engine.dispose()
    print(f"Created super administrator {user.email.value}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create-super-admin":
            return asyncio.run(run_create_super_admin(args.email, args.name))
    except DuplicateEmailError:
        print("A user with that email already exists")
        return 1
    return 2
