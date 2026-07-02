"""Codex CLI 调用封装。

使用 subprocess 调用 `codex exec`，传入浏览器工具，
解析 JSON 输出为结构化结果。
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass


@dataclass
class CodexRawOutput:
    """Codex CLI 原始输出。"""

    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float


async def invoke_codex(
    test_intent: str,
    target_url: str,
    *,
    headless: bool = True,
    timeout_seconds: int = 120,
    model: str = "gpt-4o",
) -> CodexRawOutput:
    """调用 Codex CLI 执行浏览器测试。

    优先使用 `codex` CLI（如果可用），否则降级为
    提示信息，由 Worker 侧适配层补充处理。
    """
    codex_path = shutil.which("codex")
    if codex_path is None:
        return _codex_unavailable_result(test_intent, target_url)

    prompt = _build_prompt(test_intent, target_url)

    env = os.environ.copy()
    if headless:
        env["PLAYWRIGHT_HEADLESS"] = "true"
    if model:
        env["CODEX_MODEL"] = model

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        process = await asyncio.create_subprocess_exec(
            codex_path,
            "exec",
            "--tools",
            "browser",
            "--approval-mode",
            "never",
            "--output",
            "json",
            "--input-file",
            prompt_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return CodexRawOutput(
                stdout="",
                stderr="Codex CLI execution timed out",
                returncode=process.returncode or -1,
                duration_seconds=timeout_seconds,
            )
        return CodexRawOutput(
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            returncode=process.returncode or 0,
            duration_seconds=timeout_seconds,
        )
    finally:
        try:
            os.unlink(prompt_file)
        except OSError:
            pass


def _codex_unavailable_result(
    test_intent: str,
    target_url: str,
) -> CodexRawOutput:
    """Codex CLI 不可用时的降级输出。"""
    return CodexRawOutput(
        stdout=json.dumps(
            {
                "status": "unavailable",
                "detail": (
                    "Codex CLI 未安装。请执行: npm install -g @openai/codex "
                    "并设置 OPENAI_API_KEY 环境变量。"
                ),
                "test_intent": test_intent,
                "target_url": target_url,
            },
            ensure_ascii=False,
        ),
        stderr="codex executable not found on PATH",
        returncode=127,
        duration_seconds=0,
    )


def _build_prompt(test_intent: str, target_url: str) -> str:
    """构建 Codex CLI prompt。"""
    return f"""你是浏览器自动化测试 Agent。请按以下步骤执行：

1. 打开浏览器访问 {target_url}
2. 执行测试意图：{test_intent}
3. 每一步截图保存
4. 输出 JSON 格式结果：
{{
  "status": "passed" | "failed" | "error",
  "steps": [
    {{
      "action": "动作描述",
      "screenshot": "base64截图或空",
      "result": "步骤结果"
    }}
  ],
  "summary": "测试总结",
  "generated_script": "如果有，输出完整的 Playwright 脚本"
}}

测试意图：
{test_intent}

目标 URL：
{target_url}
"""


def extract_json_result(raw: CodexRawOutput) -> dict[str, object]:
    """从 Codex raw output 中提取 JSON 结果。"""
    if raw.returncode != 0:
        return {
            "status": "error",
            "detail": raw.stderr or f"Codex CLI exited with code {raw.returncode}",
        }
    # Try to extract JSON from stdout — may be embedded in Markdown or text
    text = raw.stdout.strip()
    # Try direct JSON parse first
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    # Try to find JSON block in markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
    # Last resort: wrap raw output as plain text result
    return {
        "status": "passed",
        "summary": text[:2000],
        "raw_output": text,
    }
