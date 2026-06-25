from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.infrastructure.persistence.models import (
    ProjectMemberModel,
    ProjectModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyProjectRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, project_id: ProjectId) -> Project | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ProjectModel, project_id.value)
            if model is None:
                return None
            members = list(
                (
                    await session.scalars(
                        select(ProjectMemberModel).where(
                            ProjectMemberModel.project_id == project_id.value
                        )
                    )
                ).all()
            )
        return _to_project(model, members)

    async def list_for_user(self, user_id: UserId | None) -> list[Project]:
        statement = select(ProjectModel).order_by(ProjectModel.created_at.desc())
        if user_id is not None:
            statement = (
                statement.join(
                    ProjectMemberModel,
                    ProjectMemberModel.project_id == ProjectModel.id,
                )
                .where(ProjectMemberModel.user_id == user_id.value)
                .distinct()
            )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
            if not models:
                return []
            project_ids = [model.id for model in models]
            member_models = list(
                (
                    await session.scalars(
                        select(ProjectMemberModel).where(
                            ProjectMemberModel.project_id.in_(project_ids)
                        )
                    )
                ).all()
            )
        members_by_project: dict[UUID, list[ProjectMemberModel]] = {}
        for member in member_models:
            members_by_project.setdefault(member.project_id, []).append(member)
        return [_to_project(model, members_by_project.get(model.id, [])) for model in models]

    async def add(self, project: Project) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                ProjectModel(
                    id=project.project_id.value,
                    name=project.name,
                    description=None,
                    archived_at=project.archived_at,
                    created_at=func.now(),
                    updated_at=func.now(),
                    created_by=project.created_by.value,
                    updated_by=project.created_by.value,
                )
            )
            self._add_members(session, project)

    async def save(self, project: Project) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(ProjectModel)
                .where(ProjectModel.id == project.project_id.value)
                .values(
                    name=project.name,
                    archived_at=project.archived_at,
                    updated_at=func.now(),
                    updated_by=project.created_by.value,
                )
            )
            await session.execute(
                delete(ProjectMemberModel).where(
                    ProjectMemberModel.project_id == project.project_id.value
                )
            )
            self._add_members(session, project)

    @staticmethod
    def _add_members(session: AsyncSession, project: Project) -> None:
        for user_id, role in project.members().items():
            session.add(
                ProjectMemberModel(
                    id=uuid4(),
                    project_id=project.project_id.value,
                    user_id=user_id.value,
                    role=role.value,
                    created_at=func.now(),
                    updated_at=func.now(),
                    created_by=project.created_by.value,
                    updated_by=project.created_by.value,
                )
            )


def _to_project(
    model: ProjectModel,
    members: list[ProjectMemberModel],
) -> Project:
    project = Project(
        project_id=ProjectId(model.id),
        name=model.name,
        created_by=UserId(model.created_by),
        archived_at=model.archived_at,
    )
    for member in members:
        project.add_member(
            UserId(member.user_id),
            ProjectMemberRole(member.role),
        )
    return project
