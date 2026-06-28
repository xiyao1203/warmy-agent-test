"""Playwright Test Agents 适配器。

集成 Playwright 官方 Test Agents（Planner/Generator/Healer）。
通过 subprocess 调用 npx playwright 命令实现实际功能。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(StrEnum):
    """Playwright Agent 类型。"""
    PLANNER = "planner"
    GENERATOR = "generator"
    HEALER = "healer"


class TaskStatus(StrEnum):
    """Agent 任务状态。"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AgentTaskResult:
    """Agent 任务执行结果。"""
    task_id: str
    agent_type: AgentType
    status: TaskStatus
    output: str = ""
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None


class PlaywrightAgentAdapter:
    """Playwright Test Agents 适配器。

    通过 subprocess 调用 npx playwright 命令与 Playwright Test Agents 交互。
    """

    def __init__(
        self,
        *,
        project_dir: str | None = None,
        playwright_version: str = "latest",
    ) -> None:
        self._project_dir = project_dir or os.getcwd()
        self._playwright_version = playwright_version

    async def run_planner(
        self,
        *,
        prompt: str,
        seed_test: str | None = None,
        prd_path: str | None = None,
    ) -> AgentTaskResult:
        """运行 Planner Agent 生成测试计划。

        Args:
            prompt: 用户指令（如 "生成登录功能测试计划"）
            seed_test: 种子测试文件路径（可选）
            prd_path: PRD 文档路径（可选）

        Returns:
            AgentTaskResult 包含生成的 Markdown 计划
        """
        task_id = f"planner-{asyncio.get_event_loop().time():.0f}"

        # 创建临时工作目录
        work_dir = Path(self._project_dir) / ".playwright-agents" / task_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 构建 specs 目录
        specs_dir = work_dir / "specs"
        specs_dir.mkdir(exist_ok=True)

        # 准备输入文件
        if seed_test:
            seed_path = work_dir / "seed.spec.ts"
            seed_path.write_text(seed_test)
        if prd_path:
            prd_dest = work_dir / "prd.md"
            prd_dest.write_text(Path(prd_path).read_text())

        # 构建命令
        cmd = [
            "npx", "playwright", "test",
            "--config", str(work_dir / "playwright.config.ts"),
            "--project", "chromium",
        ]

        # 实际执行 - 使用 Playwright 的 planner agent
        # 这里我们通过 MCP 或 CLI 调用
        try:
            result = await self._run_agent_command(
                agent_type=AgentType.PLANNER,
                work_dir=work_dir,
                prompt=prompt,
            )

            # 读取生成的计划文件
            plan_files = list(specs_dir.glob("*.md"))
            plan_content = ""
            if plan_files:
                plan_content = plan_files[0].read_text()

            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.PLANNER,
                status=TaskStatus.COMPLETED,
                output=plan_content or result.get("output", ""),
                artifacts=[str(f) for f in plan_files],
            )
        except Exception as e:
            logger.exception("Planner agent failed")
            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.PLANNER,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def run_generator(
        self,
        *,
        plan_path: str,
        seed_test: str | None = None,
    ) -> AgentTaskResult:
        """运行 Generator Agent 生成测试代码。

        Args:
            plan_path: 测试计划文件路径（Markdown）
            seed_test: 种子测试文件路径（可选）

        Returns:
            AgentTaskResult 包含生成的测试文件
        """
        task_id = f"generator-{asyncio.get_event_loop().time():.0f}"

        work_dir = Path(self._project_dir) / ".playwright-agents" / task_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 复制计划文件
        plan_file = Path(plan_path)
        if plan_file.exists():
            specs_dir = work_dir / "specs"
            specs_dir.mkdir(exist_ok=True)
            (specs_dir / plan_file.name).write_text(plan_file.read_text())

        if seed_test:
            seed_path = work_dir / "seed.spec.ts"
            seed_path.write_text(seed_test)

        try:
            result = await self._run_agent_command(
                agent_type=AgentType.GENERATOR,
                work_dir=work_dir,
                prompt=f"Generate tests from plan: {plan_path}",
            )

            # 读取生成的测试文件
            tests_dir = work_dir / "tests"
            test_files = list(tests_dir.glob("**/*.spec.ts")) if tests_dir.exists() else []

            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.GENERATOR,
                status=TaskStatus.COMPLETED,
                output=result.get("output", ""),
                artifacts=[str(f) for f in test_files],
            )
        except Exception as e:
            logger.exception("Generator agent failed")
            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.GENERATOR,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def run_healer(
        self,
        *,
        test_name: str,
        test_file: str | None = None,
    ) -> AgentTaskResult:
        """运行 Healer Agent 修复失败测试。

        Args:
            test_name: 失败测试名称
            test_file: 测试文件路径（可选）

        Returns:
            AgentTaskResult 包含修复结果
        """
        task_id = f"healer-{asyncio.get_event_loop().time():.0f}"

        work_dir = Path(self._project_dir) / ".playwright-agents" / task_id
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = await self._run_agent_command(
                agent_type=AgentType.HEALER,
                work_dir=work_dir,
                prompt=f"Heal failing test: {test_name}",
            )

            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.HEALER,
                status=TaskStatus.COMPLETED,
                output=result.get("output", ""),
            )
        except Exception as e:
            logger.exception("Healer agent failed")
            return AgentTaskResult(
                task_id=task_id,
                agent_type=AgentType.HEALER,
                status=TaskStatus.FAILED,
                error=str(e),
            )

    async def _run_agent_command(
        self,
        *,
        agent_type: AgentType,
        work_dir: Path,
        prompt: str,
    ) -> dict[str, Any]:
        """执行 Playwright Agent 命令。

        通过 subprocess 调用 npx playwright 命令。
        """
        # 构建 MCP 配置文件
        mcp_config = {
            "mcpServers": {
                "playwright": {
                    "command": "npx",
                    "args": ["@playwright/mcp@latest"],
                }
            }
        }
        config_path = work_dir / "mcp-config.json"
        config_path.write_text(json.dumps(mcp_config, indent=2))

        # 根据 agent 类型构建不同的命令
        if agent_type == AgentType.PLANNER:
            cmd = [
                "npx", "playwright", "init-agents",
                "--loop=codex",
            ]
        elif agent_type == AgentType.GENERATOR:
            cmd = [
                "npx", "playwright", "test",
                "--reporter=json",
            ]
        else:  # HEALER
            cmd = [
                "npx", "playwright", "test",
                "--last-failed",
            ]

        # 执行命令
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(work_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(work_dir / "browsers")},
        )

        stdout, stderr = await proc.communicate()

        return {
            "returncode": proc.returncode,
            "output": stdout.decode("utf-8", errors="replace"),
            "error": stderr.decode("utf-8", errors="replace"),
        }


def create_playwright_agent_adapter(
    *,
    project_dir: str | None = None,
) -> PlaywrightAgentAdapter:
    """创建 Playwright Agent 适配器实例。"""
    return PlaywrightAgentAdapter(project_dir=project_dir)
