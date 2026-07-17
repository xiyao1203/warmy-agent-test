from __future__ import annotations

import builtins
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.browser_profiles.application.service import DuplicateBrowserProfile
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure.models import BrowserProfileModel


class SqlAlchemyBrowserProfileRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, item: BrowserProfile) -> None:
        try:
            async with self._session_factory() as session, session.begin():
                session.add(BrowserProfileModel(**_model_values(item)))
        except IntegrityError as error:
            raise DuplicateBrowserProfile from error

    async def save(self, item: BrowserProfile) -> None:
        try:
            async with self._session_factory() as session, session.begin():
                model = await session.scalar(
                    select(BrowserProfileModel).where(
                        BrowserProfileModel.id == item.id,
                        BrowserProfileModel.project_id == item.project_id,
                    )
                )
                if model is None:
                    raise LookupError("浏览器实例不存在")
                for key, value in _model_values(item).items():
                    if key != "id":
                        setattr(model, key, value)
        except IntegrityError as error:
            raise DuplicateBrowserProfile from error

    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None:
        async with self._session_factory() as session:
            model = await session.scalar(
                select(BrowserProfileModel).where(
                    BrowserProfileModel.id == profile_id,
                    BrowserProfileModel.project_id == project_id,
                )
            )
        return _to_domain(model) if model else None

    async def list(self, project_id: UUID) -> builtins.list[BrowserProfile]:
        async with self._session_factory() as session:
            models = list(
                (
                    await session.scalars(
                        select(BrowserProfileModel)
                        .where(BrowserProfileModel.project_id == project_id)
                        .order_by(BrowserProfileModel.updated_at.desc())
                    )
                ).all()
            )
        return [_to_domain(model) for model in models]

    async def delete(self, project_id: UUID, profile_id: UUID) -> bool:
        async with self._session_factory() as session, session.begin():
            existing = await session.scalar(
                select(BrowserProfileModel.id).where(
                    BrowserProfileModel.id == profile_id,
                    BrowserProfileModel.project_id == project_id,
                )
            )
            if existing is None:
                return False
            await session.execute(
                delete(BrowserProfileModel).where(
                    BrowserProfileModel.id == profile_id,
                    BrowserProfileModel.project_id == project_id,
                )
            )
            return True


def _model_values(item: BrowserProfile) -> dict[str, object]:
    values = asdict(item)
    values.pop("cdp_endpoint", None)
    return values


def _utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _utc_required(value: datetime) -> datetime:
    return _utc(value) or value


def _to_domain(model: BrowserProfileModel) -> BrowserProfile:
    return BrowserProfile(
        id=model.id,
        project_id=model.project_id,
        name=model.name,
        target_domain=model.target_domain,
        status=model.status,
        auth_state_status=model.auth_state_status,
        auth_state_envelope=model.auth_state_envelope,
        auth_state_sha256=model.auth_state_sha256,
        auth_state_version=model.auth_state_version,
        auth_state_updated_at=_utc(model.auth_state_updated_at),
        last_login_at=_utc(model.last_login_at),
        last_verified_at=_utc(model.last_verified_at),
        user_data_dir=model.user_data_dir,
        cdp_port=model.cdp_port,
        cdp_endpoint="",
        locked_by_run_case_id=model.locked_by_run_case_id,
        locked_at=_utc(model.locked_at),
        created_by=model.created_by,
        created_at=_utc_required(model.created_at),
        updated_at=_utc_required(model.updated_at),
    )
