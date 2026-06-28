"""Playwright Test Agents 集成测试。"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agenttest.modules.test_agent.adapters.playwright_agents import (
    AgentType,
    AgentTaskResult,
    PlaywrightAgentAdapter,
    TaskStatus,
    create_playwright_agent_adapter,
)


def test_agent_type_enum():
    """测试 Agent 类型枚举。"""
    assert AgentType.PLANNER == "planner"
    assert AgentType.GENERATOR == "generator"
    assert AgentType.HEALER == "healer"


def test_task_status_enum():
    """测试任务状态枚举。"""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.RUNNING == "running"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


def test_create_adapter():
    """测试创建适配器实例。"""
    adapter = create_playwright_agent_adapter()
    assert adapter is not None
    assert isinstance(adapter, PlaywrightAgentAdapter)


def test_adapter_custom_project_dir():
    """测试自定义项目目录。"""
    adapter = create_playwright_agent_adapter(project_dir="/tmp/test")
    assert adapter._project_dir == "/tmp/test"


@pytest.mark.asyncio
async def test_planner_task_result():
    """测试 Planner 任务结果结构。"""
    result = AgentTaskResult(
        task_id="test-123",
        agent_type=AgentType.PLANNER,
        status=TaskStatus.COMPLETED,
        output="# Test Plan\n\n## Scenario 1",
        artifacts=["specs/plan.md"],
    )

    assert result.task_id == "test-123"
    assert result.agent_type == AgentType.PLANNER
    assert result.status == TaskStatus.COMPLETED
    assert "Test Plan" in result.output
    assert len(result.artifacts) == 1


@pytest.mark.asyncio
async def test_generator_task_result():
    """测试 Generator 任务结果结构。"""
    result = AgentTaskResult(
        task_id="test-456",
        agent_type=AgentType.GENERATOR,
        status=TaskStatus.COMPLETED,
        output="Generated 3 tests",
        artifacts=["tests/test1.spec.ts", "tests/test2.spec.ts"],
    )

    assert result.task_id == "test-456"
    assert result.agent_type == AgentType.GENERATOR
    assert len(result.artifacts) == 2


@pytest.mark.asyncio
async def test_healer_task_result():
    """测试 Healer 任务结果结构。"""
    result = AgentTaskResult(
        task_id="test-789",
        agent_type=AgentType.HEALER,
        status=TaskStatus.COMPLETED,
        output="Test healed successfully",
    )

    assert result.task_id == "test-789"
    assert result.agent_type == AgentType.HEALER
    assert result.error is None


@pytest.mark.asyncio
async def test_failed_task_result():
    """测试失败任务结果。"""
    result = AgentTaskResult(
        task_id="test-fail",
        agent_type=AgentType.PLANNER,
        status=TaskStatus.FAILED,
        error="Playwright not installed",
    )

    assert result.status == TaskStatus.FAILED
    assert result.error == "Playwright not installed"


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_agent_command_success(mock_subprocess):
    """测试成功执行 Agent 命令。"""
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Success output", b"")
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    adapter = PlaywrightAgentAdapter(project_dir="/tmp/test")
    result = await adapter._run_agent_command(
        agent_type=AgentType.PLANNER,
        work_dir=MagicMock(),
        prompt="Generate plan",
    )

    assert result["returncode"] == 0
    assert "Success output" in result["output"]


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_agent_command_failure(mock_subprocess):
    """测试命令执行失败。"""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Error: command failed")
    mock_process.returncode = 1
    mock_subprocess.return_value = mock_process

    adapter = PlaywrightAgentAdapter(project_dir="/tmp/test")
    result = await adapter._run_agent_command(
        agent_type=AgentType.GENERATOR,
        work_dir=MagicMock(),
        prompt="Generate tests",
    )

    assert result["returncode"] == 1
    assert "Error" in result["error"]


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_planner_integration(mock_subprocess):
    """测试 Planner Agent 集成。"""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Plan generated", b"")
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    adapter = PlaywrightAgentAdapter(project_dir="/tmp/test")

    # Mock the _run_agent_command method
    with patch.object(adapter, "_run_agent_command", return_value={"output": "Plan generated", "returncode": 0}):
        result = await adapter.run_planner(
            prompt="Generate login test plan",
        )

    assert result.agent_type == AgentType.PLANNER
    assert result.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_generator_integration(mock_subprocess):
    """测试 Generator Agent 集成。"""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Tests generated", b"")
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    adapter = PlaywrightAgentAdapter(project_dir="/tmp/test")

    with patch.object(adapter, "_run_agent_command", return_value={"output": "Tests generated", "returncode": 0}):
        result = await adapter.run_generator(
            plan_path="/tmp/plan.md",
        )

    assert result.agent_type == AgentType.GENERATOR
    assert result.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_run_healer_integration(mock_subprocess):
    """测试 Healer Agent 集成。"""
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"Test healed", b"")
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    adapter = PlaywrightAgentAdapter(project_dir="/tmp/test")

    with patch.object(adapter, "_run_agent_command", return_value={"output": "Test healed", "returncode": 0}):
        result = await adapter.run_healer(
            test_name="test-login",
        )

    assert result.agent_type == AgentType.HEALER
    assert result.status == TaskStatus.COMPLETED
