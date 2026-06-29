"""项目级大模型配置 SQLAlchemy 仓库。"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope

from ...domain.entities import ModelConfiguration, ModelConfigurationId, ProjectModelDefault
from ...domain.value_objects import ModelPurpose, ProviderType
from .models import ModelConfigurationModel, ProjectModelDefaultModel


class SqlAlchemyModelConfigRepository:
    """按 `project_id` 强制过滤的模型配置仓库。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_by_project(self, project_id: ProjectId) -> list[ModelConfiguration]:
        statement = (
            select(ModelConfigurationModel)
            .where(
                ModelConfigurationModel.project_id == project_id.value,
            )
            .order_by(ModelConfigurationModel.created_at.desc())
        )
        async with session_scope(self._session_factory) as session:
            values = list((await session.scalars(statement)).all())
        return [_to_domain(value) for value in values]

    async def get(
        self,
        project_id: ProjectId,
        model_config_id: ModelConfigurationId,
    ) -> ModelConfiguration | None:
        statement = select(ModelConfigurationModel).where(
            ModelConfigurationModel.project_id == project_id.value,
            ModelConfigurationModel.id == model_config_id.value,
        )
        async with session_scope(self._session_factory) as session:
            value = await session.scalar(statement)
        return _to_domain(value) if value else None

    async def add(self, item: ModelConfiguration) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(_to_model(item))

    async def save(self, item: ModelConfiguration) -> None:
        async with transaction_scope(self._session_factory) as session:
            model = await session.get(ModelConfigurationModel, item.model_config_id.value)
            if model is None or model.project_id != item.project_id.value:
                return
            model.name = item.name
            model.base_url = item.base_url
            model.model_name = item.model_name
            model.encrypted_api_key = item.encrypted_api_key
            model.api_key_hint = item.api_key_hint
            model.supports_vision = item.supports_vision
            model.enabled = item.enabled
            model.updated_at = item.updated_at

    async def delete(
        self,
        project_id: ProjectId,
        model_config_id: ModelConfigurationId,
    ) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(ModelConfigurationModel).where(
                    ModelConfigurationModel.project_id == project_id.value,
                    ModelConfigurationModel.id == model_config_id.value,
                )
            )

    async def list_defaults(self, project_id: ProjectId) -> list[ProjectModelDefault]:
        statement = (
            select(ProjectModelDefaultModel)
            .where(
                ProjectModelDefaultModel.project_id == project_id.value,
            )
            .order_by(ProjectModelDefaultModel.purpose)
        )
        async with session_scope(self._session_factory) as session:
            values = list((await session.scalars(statement)).all())
        return [_default_to_domain(value) for value in values]

    async def get_default(
        self,
        project_id: ProjectId,
        purpose: ModelPurpose,
    ) -> ProjectModelDefault | None:
        async with session_scope(self._session_factory) as session:
            value = await session.get(
                ProjectModelDefaultModel,
                (project_id.value, purpose.value),
            )
        return _default_to_domain(value) if value else None

    async def set_default(self, value: ProjectModelDefault) -> None:
        async with transaction_scope(self._session_factory) as session:
            model = await session.get(
                ProjectModelDefaultModel,
                (value.project_id.value, value.purpose.value),
            )
            if model is None:
                session.add(
                    ProjectModelDefaultModel(
                        project_id=value.project_id.value,
                        purpose=value.purpose.value,
                        model_config_id=value.model_config_id.value,
                        updated_by=value.updated_by.value,
                        updated_at=value.updated_at,
                    )
                )
            else:
                model.model_config_id = value.model_config_id.value
                model.updated_by = value.updated_by.value
                model.updated_at = value.updated_at

    async def is_default(
        self,
        project_id: ProjectId,
        model_config_id: ModelConfigurationId,
    ) -> bool:
        statement = (
            select(ProjectModelDefaultModel.project_id)
            .where(
                ProjectModelDefaultModel.project_id == project_id.value,
                ProjectModelDefaultModel.model_config_id == model_config_id.value,
            )
            .limit(1)
        )
        async with session_scope(self._session_factory) as session:
            return await session.scalar(statement) is not None


def _to_model(item: ModelConfiguration) -> ModelConfigurationModel:
    return ModelConfigurationModel(
        id=item.model_config_id.value,
        project_id=item.project_id.value,
        name=item.name,
        provider_type=item.provider_type.value,
        base_url=item.base_url,
        model_name=item.model_name,
        encrypted_api_key=item.encrypted_api_key,
        api_key_hint=item.api_key_hint,
        supports_text=item.supports_text,
        supports_vision=item.supports_vision,
        enabled=item.enabled,
        created_by=item.created_by.value,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_domain(value: ModelConfigurationModel) -> ModelConfiguration:
    return ModelConfiguration(
        model_config_id=ModelConfigurationId(value.id),
        project_id=ProjectId(value.project_id),
        name=value.name,
        provider_type=ProviderType(value.provider_type),
        base_url=value.base_url,
        model_name=value.model_name,
        encrypted_api_key=value.encrypted_api_key,
        api_key_hint=value.api_key_hint,
        supports_text=value.supports_text,
        supports_vision=value.supports_vision,
        enabled=value.enabled,
        created_by=UserId(value.created_by),
        created_at=value.created_at,
        updated_at=value.updated_at,
    )


def _default_to_domain(value: ProjectModelDefaultModel) -> ProjectModelDefault:
    return ProjectModelDefault(
        project_id=ProjectId(value.project_id),
        purpose=ModelPurpose(value.purpose),
        model_config_id=ModelConfigurationId(value.model_config_id),
        updated_by=UserId(value.updated_by),
        updated_at=value.updated_at,
    )
