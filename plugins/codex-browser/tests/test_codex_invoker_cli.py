from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from agenttest_plugin_codex.codex_invoker import invoke_codex


@pytest.mark.asyncio
async def test_invoke_codex_uses_current_exec_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr("shutil.which", lambda name: "/bin/codex" if name == "codex" else None)

    class FakeProcess:
        returncode = 0

        async def communicate(self, stdin: bytes | None = None) -> tuple[bytes, bytes]:
            captured["stdin"] = stdin
            output_path = captured["args"][captured["args"].index("--output-last-message") + 1]
            await asyncio.to_thread(
                Path(output_path).write_text,
                '{"status":"passed","detail":"ok"}',
            )
            return b"transcript", b""

        def kill(self) -> None:
            captured["killed"] = True

        async def wait(self) -> None:
            captured["waited"] = True

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> FakeProcess:
        captured["args"] = list(args)
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    raw = await invoke_codex(
        test_intent="检查页面标题",
        target_url="about:blank",
        model="",
    )

    args = captured["args"]
    assert raw.returncode == 0
    assert raw.stdout == '{"status":"passed","detail":"ok"}'
    assert "--output-last-message" in args
    assert "--sandbox" in args
    assert "--model" not in args
    assert "--tools" not in args
    assert "--approval-mode" not in args
    assert "--input-file" not in args
    assert "--cdp-endpoint" not in args
    assert "--storage-state" not in args
    assert captured["kwargs"]["stdin"] is asyncio.subprocess.PIPE
    assert captured["kwargs"]["start_new_session"] is True
    assert b"about:blank" in captured["stdin"]


@pytest.mark.asyncio
async def test_invoke_codex_passes_explicit_model_and_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr("shutil.which", lambda name: "/bin/codex" if name == "codex" else None)

    class FakeProcess:
        returncode = 0

        async def communicate(self, stdin: bytes | None = None) -> tuple[bytes, bytes]:
            output_path = captured["args"][captured["args"].index("--output-last-message") + 1]
            await asyncio.to_thread(Path(output_path).write_text, '{"status":"passed"}')
            return b"", b""

        def kill(self) -> None:
            pass

        async def wait(self) -> None:
            pass

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> FakeProcess:
        captured["args"] = list(args)
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    await invoke_codex(
        test_intent="检查页面标题",
        target_url="about:blank",
        model="gpt-5.5",
        model_provider="OpenAI",
    )

    assert "--model" in captured["args"]
    assert "gpt-5.5" in captured["args"]
    assert "--config" in captured["args"]
    assert 'model_provider="OpenAI"' in captured["args"]


@pytest.mark.asyncio
async def test_invoke_codex_times_out_and_kills_process_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    monkeypatch.setattr("shutil.which", lambda name: "/bin/codex" if name == "codex" else None)
    monkeypatch.setattr(
        "agenttest_plugin_codex.codex_invoker._kill_process_group",
        lambda pid: captured.update(killed_pid=pid),
    )

    class FakeProcess:
        pid = 12345
        returncode: int | None = None

        async def communicate(self, stdin: bytes | None = None) -> tuple[bytes, bytes]:
            await asyncio.Event().wait()
            return b"", b""

        def kill(self) -> None:
            captured["fallback_kill"] = True

        async def wait(self) -> None:
            self.returncode = -9

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    raw = await invoke_codex(
        test_intent="检查页面标题",
        target_url="about:blank",
        timeout_seconds=0,
    )

    assert raw.returncode == -9
    assert raw.stderr == "Codex CLI execution timed out"
    assert captured["killed_pid"] == 12345
