"""安全策略 ORM 与持久化。"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from agenttest.modules.security.domain.models import (
    ScanStatus,
    SecurityPolicy,
    SecurityScan,
)
from agenttest.shared.infrastructure.database import Base


class SecurityPolicyModel(Base):
    __tablename__ = "security_policies"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    blocked_tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    require_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )


def _to_domain(row: SecurityPolicyModel) -> SecurityPolicy:
    return SecurityPolicy(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        max_steps=row.max_steps,
        timeout_seconds=row.timeout_seconds,
        blocked_tools=list(row.blocked_tools) if row.blocked_tools else [],
        require_confirmation=row.require_confirmation,
        enabled=row.enabled,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemySecurityPolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, policy: SecurityPolicy, *, project_id: UUID) -> None:
        row = SecurityPolicyModel(
            id=policy.id,
            project_id=project_id,
            name=policy.name,
            max_steps=policy.max_steps,
            timeout_seconds=policy.timeout_seconds,
            blocked_tools=policy.blocked_tools,
            require_confirmation=policy.require_confirmation,
            enabled=policy.enabled,
        )
        self._session.add(row)
        await self._session.flush()

    async def get(self, policy_id: UUID, *, project_id: UUID) -> SecurityPolicy | None:
        row = await self._session.get(SecurityPolicyModel, policy_id)
        if row is None or row.project_id != project_id:
            return None
        return _to_domain(row)

    async def get_default(self, *, project_id: UUID) -> SecurityPolicy | None:
        stmt = (
            select(SecurityPolicyModel)
            .where(SecurityPolicyModel.project_id == project_id)
            .where(SecurityPolicyModel.enabled.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_all(self, *, project_id: UUID) -> list[SecurityPolicy]:
        stmt = (
            select(SecurityPolicyModel)
            .where(SecurityPolicyModel.project_id == project_id)
            .order_by(SecurityPolicyModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_to_domain(r) for r in result.scalars().all()]


# ── Security Scan ─────────────────────────────────────────────────────────


class SecurityScanModel(Base):
    __tablename__ = "security_scans"
    __table_args__ = ()

    id = mapped_column(primary_key=True)
    project_id = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    scan_type: Mapped[str] = mapped_column(String(64), nullable=False, default="full")
    findings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )


class SqlAlchemySecurityScanRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, scan: SecurityScan) -> None:
        async with self._session_factory() as session:
            session.add(SecurityScanModel(
                id=scan.scan_id,
                project_id=scan.project_id,
                status=scan.status.value,
                scan_type=scan.scan_type,
                findings=scan.findings,
                summary=scan.summary,
                created_at=scan.created_at,
                updated_at=scan.updated_at,
                completed_at=scan.completed_at,
            ))
            await session.commit()

    async def get_by_id_and_project(
        self, scan_id: UUID, project_id: UUID,
    ) -> SecurityScan | None:
        async with self._session_factory() as session:
            row = await session.get(SecurityScanModel, scan_id)
            if row is None or row.project_id != project_id:
                return None
            return _scan_to_domain(row)

    async def list_by_project(
        self, project_id: UUID, *, limit: int = 50,
    ) -> list[SecurityScan]:
        async with self._session_factory() as session:
            stmt = (
                select(SecurityScanModel)
                .where(SecurityScanModel.project_id == project_id)
                .order_by(SecurityScanModel.created_at.desc())
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [_scan_to_domain(r) for r in rows]

    async def save(self, scan: SecurityScan) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    "UPDATE security_scans SET status=:s, findings=:f, "
                    "summary=:sum, updated_at=:u, completed_at=:c WHERE id=:id"
                ),
                {
                    "id": scan.scan_id,
                    "s": scan.status.value,
                    "f": scan.findings,
                    "sum": scan.summary,
                    "u": scan.updated_at,
                    "c": scan.completed_at,
                },
            )
            await session.commit()


def _scan_to_domain(row: SecurityScanModel) -> SecurityScan:
    return SecurityScan(
        scan_id=row.id,
        project_id=row.project_id,
        status=ScanStatus(row.status),
        scan_type=row.scan_type,
        findings=list(row.findings) if isinstance(row.findings, list) else [],
        summary=dict(row.summary) if isinstance(row.summary, dict) else {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )
