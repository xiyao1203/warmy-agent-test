"""Agent 领域实体。

定义 Agent 聚合根和 AgentVersion 实体：
- Agent：项目下的 AI Agent 聚合根，管理名称、类型和元数据。
- AgentVersion：Agent 的配置版本，支持草稿/发布状态和不可变版本机制。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class AgentId:
    """Agent 聚合根的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> AgentId:
        """生成新的 AgentId。"""
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class AgentVersionId:
    """Agent 版本实体的唯一标识。"""

    value: UUID

    @classmethod
    def new(cls) -> AgentVersionId:
        """生成新的 AgentVersionId。"""
        return cls(uuid4())


@dataclass(slots=True)
class Agent:
    """项目下的 AI Agent 聚合根。

    管理 Agent 的核心元数据（名称、类型、描述），不包含具体配置——
    配置通过 AgentVersion 进行版本化管理。

    Attributes:
        agent_id: Agent 唯一标识。
        project_id: 所属项目 ID，保证项目间数据隔离。
        name: Agent 名称。
        agent_type: Agent 类型，如 generic_http 或 canvas。
        created_by: 创建者用户 ID。
        updated_by: 最后修改者用户 ID。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
        description: 可选的 Agent 描述。
    """

    agent_id: AgentId
    project_id: ProjectId
    name: str
    agent_type: AgentType
    created_by: UserId
    updated_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    current_version_id: AgentVersionId | None = None
    baseline_version_id: AgentVersionId | None = None

    @classmethod
    def create(
        cls,
        *,
        agent_id: AgentId,
        project_id: ProjectId,
        name: str,
        agent_type: AgentType,
        created_by: UserId,
        description: str | None = None,
    ) -> Agent:
        """创建新的 Agent 聚合根。

        Args:
            agent_id: 预生成的 Agent ID。
            project_id: 所属项目 ID。
            name: Agent 名称，不可为空。
            agent_type: Agent 类型枚举。
            created_by: 创建者用户 ID。
            description: 可选的描述文本。

        Returns:
            新创建的 Agent 实体。

        Raises:
            ValueError: name 为空或仅含空白字符时抛出。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Agent name is required")
        now = datetime.now(UTC)
        return cls(
            agent_id=agent_id,
            project_id=project_id,
            name=normalized_name,
            agent_type=agent_type,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        """修改 Agent 名称。

        Args:
            name: 新名称，不可为空。

        Raises:
            ValueError: name 为空或仅含空白字符时抛出。
        """
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Agent name is required")
        self.name = normalized_name
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        """更新 Agent 描述，同时刷新 updated_at。"""
        self.description = description
        self.updated_at = datetime.now(UTC)

    def set_current_version(self, version_id: AgentVersionId) -> None:
        """设置当前版本 ID。"""
        self.current_version_id = version_id
        self.updated_at = datetime.now(UTC)

    def set_baseline_version(self, version_id: AgentVersionId) -> None:
        """设置基线版本 ID。"""
        self.baseline_version_id = version_id
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class AgentVersion:
    """Agent 的配置版本实体。

    每个 Agent 可以有多个版本。版本发布后不可修改——
    任何配置变更必须创建新的草稿版本。

    状态转换：
        DRAFT → PUBLISHED（单向，不可逆）

    Attributes:
        version_id: 版本唯一标识。
        agent_id: 所属 Agent ID。
        version_number: 版本号，从 1 开始自增。
        status: 版本状态（draft 或 published）。
        config: Agent 配置对象（api_url、model、超时等）。
        created_by: 创建者用户 ID。
        created_at: 创建时间（UTC）。
        updated_at: 最后更新时间（UTC）。
        published_at: 发布时间，仅已发布版本有值。
    """

    version_id: AgentVersionId
    agent_id: AgentId
    version_number: int
    status: VersionStatus
    config: AgentConfig
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    @classmethod
    def create_draft(
        cls,
        *,
        version_id: AgentVersionId,
        agent_id: AgentId,
        version_number: int,
        config: AgentConfig,
        created_by: UserId,
    ) -> AgentVersion:
        """创建新的草稿版本。

        新版本初始状态为 DRAFT，发布时间为 None。

        Args:
            version_id: 预生成的版本 ID。
            agent_id: 所属 Agent ID。
            version_number: 版本号，必须 >= 1。
            config: Agent 配置。
            created_by: 创建者用户 ID。

        Returns:
            新创建的草稿版本。

        Raises:
            ValueError: version_number < 1 时抛出。
        """
        if version_number < 1:
            raise ValueError("version_number must be >= 1")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            agent_id=agent_id,
            version_number=version_number,
            status=VersionStatus.DRAFT,
            config=config,
            published_at=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_editable(self) -> bool:
        """仅草稿版本可编辑，已发布版本不可修改。"""
        return self.status is VersionStatus.DRAFT

    @property
    def is_published(self) -> bool:
        """版本是否已发布。"""
        return self.status is VersionStatus.PUBLISHED

    def publish(self) -> None:
        """将草稿版本发布为正式版本。

        发布后版本不可修改——任何配置变更必须创建新草稿。
        记录发布时间并更新 updated_at。

        Raises:
            ValueError: 版本已经发布时抛出。
        """
        if self.status is VersionStatus.PUBLISHED:
            raise ValueError("Version is already published")
        self.status = VersionStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.updated_at = self.published_at

    def update_config(self, config: AgentConfig) -> None:
        """更新草稿版本的配置。

        仅草稿版本可调用此方法。

        Args:
            config: 新的 Agent 配置对象。

        Raises:
            ValueError: 尝试修改已发布版本时抛出。
        """
        if not self.is_editable:
            raise ValueError("Cannot modify a published version")
        self.config = config
        self.updated_at = datetime.now(UTC)

    @classmethod
    def create_new_version_from(
        cls,
        *,
        version_id: AgentVersionId,
        source: AgentVersion,
        new_version_number: int,
    ) -> AgentVersion:
        """从已发布版本创建新草稿。

        新草稿继承源版本的配置，但状态为 DRAFT、无发布时间，
        确保两个版本后续独立演化。

        Args:
            version_id: 新版本的预生成 ID。
            source: 已发布的源版本。
            new_version_number: 新版本号。

        Returns:
            继承源配置的新草稿版本。

        Raises:
            ValueError: 源版本未发布时抛出。
        """
        if not source.is_published:
            raise ValueError("Can only create a new version from a published version")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            agent_id=source.agent_id,
            version_number=new_version_number,
            status=VersionStatus.DRAFT,
            config=source.config,
            published_at=None,
            created_by=source.created_by,
            created_at=now,
            updated_at=now,
        )
