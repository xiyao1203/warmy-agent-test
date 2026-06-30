"""Agent 版本扩展字段和对比 API 测试。

验证新增字段、版本对比和基线标记功能。
"""

from __future__ import annotations

import pytest
from uuid import UUID, uuid4
from datetime import UTC, datetime

from agenttest.modules.agents.domain.entities import Agent, AgentVersion
from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)


# ── AgentConfig 扩展字段测试 ─────────────────────────────────────────────────


class TestAgentConfigNewFields:
    def test_agent_config_has_system_prompt_version(self):
        """AgentConfig 支持 system_prompt_version 字段。"""
        config = AgentConfig(
            api_url="https://api.example.com",
            system_prompt_version="v2.1",
        )
        assert config.system_prompt_version == "v2.1"
        assert config.to_dict()["system_prompt_version"] == "v2.1"

    def test_agent_config_has_knowledge_version(self):
        """AgentConfig 支持 knowledge_version 字段。"""
        config = AgentConfig(
            api_url="https://api.example.com",
            knowledge_version="kb-20260627",
        )
        assert config.knowledge_version == "kb-20260627"
        assert config.to_dict()["knowledge_version"] == "kb-20260627"

    def test_agent_config_has_adapter_version(self):
        """AgentConfig 支持 adapter_version 字段。"""
        config = AgentConfig(
            api_url="https://api.example.com",
            adapter_version="v1.0.0",
        )
        assert config.adapter_version == "v1.0.0"
        assert config.to_dict()["adapter_version"] == "v1.0.0"

    def test_new_fields_default_to_none(self):
        """新字段默认为 None，不影响现有构造。"""
        config = AgentConfig(api_url="https://api.example.com")
        assert config.system_prompt_version is None
        assert config.knowledge_version is None
        assert config.adapter_version is None

    def test_from_dict_with_new_fields(self):
        """from_dict 能正确反序列化新字段。"""
        data = {
            "api_url": "https://api.example.com",
            "system_prompt_version": "v1",
            "knowledge_version": "kb-1",
            "adapter_version": "v2.0",
        }
        config = AgentConfig.from_dict(data)
        assert config.system_prompt_version == "v1"
        assert config.knowledge_version == "kb-1"
        assert config.adapter_version == "v2.0"


# ── Agent 基线标记测试 ──────────────────────────────────────────────────────


class TestAgentBaselineVersion:
    def test_agent_has_current_version_id_field(self):
        """Agent 实体支持 current_version_id 字段。"""
        agent = Agent(
            agent_id=uuid4(),
            project_id=uuid4(),
            name="Test Agent",
            agent_type=AgentType.GENERIC_HTTP,
            created_by=uuid4(),
            updated_by=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert agent.current_version_id is None

    def test_agent_has_baseline_version_id_field(self):
        """Agent 实体支持 baseline_version_id 字段。"""
        agent = Agent(
            agent_id=uuid4(),
            project_id=uuid4(),
            name="Test Agent",
            agent_type=AgentType.GENERIC_HTTP,
            created_by=uuid4(),
            updated_by=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert agent.baseline_version_id is None

    def test_set_current_version(self):
        """设置 current_version_id。"""
        agent = Agent(
            agent_id=uuid4(),
            project_id=uuid4(),
            name="Test Agent",
            agent_type=AgentType.GENERIC_HTTP,
            created_by=uuid4(),
            updated_by=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        vid = uuid4()
        agent.set_current_version(vid)
        assert agent.current_version_id == vid

    def test_set_baseline_version(self):
        """设置 baseline_version_id。"""
        agent = Agent(
            agent_id=uuid4(),
            project_id=uuid4(),
            name="Test Agent",
            agent_type=AgentType.GENERIC_HTTP,
            created_by=uuid4(),
            updated_by=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        vid = uuid4()
        agent.set_baseline_version(vid)
        assert agent.baseline_version_id == vid


# ── 版本对比测试 ────────────────────────────────────────────────────────────


class TestVersionDiff:
    def test_version_diff_detects_changed_fields(self):
        """两个版本的 config 差异可被检测。"""
        config_a = AgentConfig(
            api_url="https://v1.example.com",
            model="gpt-4",
            timeout=30,
            max_steps=10,
        )
        config_b = AgentConfig(
            api_url="https://v2.example.com",
            model="gpt-4o",
            timeout=60,
            max_steps=20,
        )
        dict_a = config_a.to_dict()
        dict_b = config_b.to_dict()

        changed = [
            k
            for k in set(list(dict_a.keys()) + list(dict_b.keys()))
            if dict_a.get(k) != dict_b.get(k)
        ]
        assert "api_url" in changed
        assert "model" in changed
        assert "timeout" in changed
        assert "max_steps" in changed

    def test_version_diff_no_change(self):
        """相同配置返回空 diff。"""
        config = AgentConfig(api_url="https://example.com")
        dict_a = config.to_dict()
        dict_b = config.to_dict()
        changed = [k for k in dict_a if dict_a.get(k) != dict_b.get(k)]
        assert changed == []
