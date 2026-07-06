"""Browser Profile CRUD API。

提供浏览器实例的增删改查 HTTP 端点，存储与插件层
profile_registry.py 共享同一套 JSON 文件。
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── 数据模型 ──────────────────────────────────────────────


class CreateBrowserProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_domain: str = ""
    user_data_dir: str = ""


class UpdateBrowserProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_domain: str | None = None


class StartBrowserProfileRequest(BaseModel):
    login_url: str = ""


class CompleteBrowserProfileLoginRequest(BaseModel):
    stop_after_save: bool = False


class ProfileResponse(BaseModel):
    profile_id: str
    project_id: str
    name: str
    target_domain: str
    user_data_dir: str
    storage_state_path: str
    cdp_port: int
    status: str
    cdp_endpoint: str
    created_at: str
    updated_at: str
    last_login_at: str = ""


class ProfileListResponse(BaseModel):
    items: list[ProfileResponse]


# ── 存储路径（与插件 profile_registry.py 一致）────────────


def _registry_root() -> Path:
    return Path.home() / ".agenttest" / "browser-profiles"


def _registry_path(project_id: str) -> Path:
    root = _registry_root()
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{project_id}.json"


def _default_profile_dir(profile_id: str) -> str:
    return str(_registry_root() / "data" / profile_id)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ── 文件 I/O ─────────────────────────────────────────────


def _load_all(project_id: str) -> list[dict]:
    path = _registry_path(project_id)
    if not path.exists():
        return []
    try:
        with open(path) as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(project_id: str, data: list[dict]) -> None:
    path = _registry_path(project_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _find_free_port(start: int = 9222) -> int:
    port = start
    while port < start + 1000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("无法找到空闲端口")


def _used_ports(project_id: str) -> set[int]:
    try:
        return {p["cdp_port"] for p in _load_all(project_id)}
    except Exception:
        return set()


_running_processes: dict[str, subprocess.Popen] = {}


def _to_response(data: dict) -> ProfileResponse:
    return ProfileResponse(
        profile_id=data["profile_id"],
        project_id=data["project_id"],
        name=data["name"],
        target_domain=data.get("target_domain", ""),
        user_data_dir=data["user_data_dir"],
        storage_state_path=data.get("storage_state_path", ""),
        cdp_port=data.get("cdp_port", 0),
        status=data.get("status", "stopped"),
        cdp_endpoint=data.get("cdp_endpoint", ""),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        last_login_at=data.get("last_login_at", ""),
    )


def _update_profile_fields(project_id: str, profile_id: str, **fields) -> dict | None:
    profiles = _load_all(project_id)
    for data in profiles:
        if data["profile_id"] == profile_id:
            allowed = {
                "name",
                "target_domain",
                "status",
                "cdp_endpoint",
                "cdp_port",
                "last_login_at",
            }
            for key, value in fields.items():
                if key in allowed:
                    data[key] = value
            data["updated_at"] = _now_iso()
            _save_all(project_id, profiles)
            return data
    return None


def _browser_candidates() -> list[str]:
    configured = os.environ.get("AGENTTEST_CHROME_PATH", "").strip()
    candidates: list[str] = [configured] if configured else []
    candidates.extend(
        [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            shutil.which("google-chrome") or "",
            shutil.which("chromium") or "",
            shutil.which("chromium-browser") or "",
            shutil.which("chrome") or "",
        ]
    )
    return [candidate for candidate in candidates if candidate]


def _find_browser_executable() -> str:
    for candidate in _browser_candidates():
        path = Path(candidate)
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
    raise RuntimeError("未找到 Chrome/Chromium，请安装浏览器或设置 AGENTTEST_CHROME_PATH")


def _normalise_login_url(login_url: str, target_domain: str) -> str:
    value = (login_url or target_domain or "").strip()
    if not value:
        return ""
    if re.match(r"^https?://", value, flags=re.IGNORECASE):
        return value
    return f"https://{value}"


def _read_cdp_endpoint(port: int) -> str:
    with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=0.5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    endpoint = payload.get("webSocketDebuggerUrl")
    if not isinstance(endpoint, str) or not endpoint:
        raise RuntimeError("Chrome 已启动但未返回 CDP 地址")
    return endpoint


def _open_cdp_url(port: int, url: str) -> None:
    if not url:
        return
    target = f"http://127.0.0.1:{port}/json/new?{quote(url, safe='')}"
    last_error: Exception | None = None
    for method in ("PUT", "POST", "GET"):
        try:
            request = UrlRequest(target, method=method)
            with urlopen(request, timeout=1) as response:
                response.read()
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"无法通过 CDP 打开登录页: {last_error}")


def _wait_for_cdp(port: int, timeout_seconds: float = 10) -> str:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return _read_cdp_endpoint(port)
        except (OSError, RuntimeError, URLError) as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"Chrome 启动超时，无法连接端口 {port}: {last_error}")


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _replace_profile_port(data: dict) -> int:
    project_id = data.get("project_id", "")
    current = int(data.get("cdp_port") or 0)
    used = _used_ports(project_id)
    used.discard(current)
    candidate = _find_free_port(max(9222, current + 1))
    while candidate in used:
        candidate = _find_free_port(candidate + 1)
    data["cdp_port"] = candidate
    return candidate


def _launch_browser_profile(data: dict, login_url: str) -> str:
    profile_id = data["profile_id"]
    port = int(data.get("cdp_port") or 0)
    if port <= 0:
        raise RuntimeError("浏览器实例缺少调试端口")
    url = _normalise_login_url(login_url, data.get("target_domain", ""))

    process = _running_processes.get(profile_id)
    if process is not None and process.poll() is None:
        try:
            endpoint = _read_cdp_endpoint(port)
        except Exception:
            process.kill()
            _running_processes.pop(profile_id, None)
        else:
            _open_cdp_url(port, url)
            return endpoint

    if data.get("status") == "running":
        try:
            endpoint = _read_cdp_endpoint(port)
        except Exception:
            pass
        else:
            _open_cdp_url(port, url)
            return endpoint

    if not _is_port_free(port):
        port = _replace_profile_port(data)

    executable = _find_browser_executable()
    Path(data["user_data_dir"]).mkdir(parents=True, exist_ok=True)
    args = [
        executable,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={data['user_data_dir']}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if url:
        args.append("--new-window")
        args.append(url)

    process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _running_processes[profile_id] = process
    try:
        return _wait_for_cdp(port)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
        _running_processes.pop(profile_id, None)
        raise


def _stop_browser_profile(profile_id: str) -> None:
    process = _running_processes.pop(profile_id, None)
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


# ── Router 工厂 ───────────────────────────────────────────


def create_browser_profile_router(
    *,
    settings,  # Settings
    actor_for: Callable,  # async (Request) -> User | None
    check_project: Callable,  # async (project_id) -> None
) -> APIRouter:
    router = APIRouter(tags=["browser-profiles"])

    CSRF_NAME = "agenttest_csrf"

    async def _actor(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await actor_for(request)

    def _csrf_ok(request: Request) -> bool:
        header = request.headers.get("X-Csrf-Token")
        cookie = request.cookies.get(CSRF_NAME)
        return bool(header) and header == cookie

    # ── GET /projects/{project_id}/browser-profiles ──────

    @router.get("/api/v1/projects/{project_id}/browser-profiles")
    async def list_profiles(request: Request, project_id: str):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        items = [_to_response(d) for d in _load_all(project_id)]
        return {"items": [item.model_dump() for item in items]}

    # ── POST /projects/{project_id}/browser-profiles ─────

    @router.post("/api/v1/projects/{project_id}/browser-profiles", status_code=201)
    async def create_profile(
        request: Request,
        project_id: str,
        body: CreateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profile_id = str(uuid.uuid4())
        user_data_dir = body.user_data_dir or _default_profile_dir(profile_id)
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240

        used = _used_ports(project_id)
        free = _find_free_port(9222)
        while free in used:
            free = _find_free_port(free + 1)

        now = _now_iso()
        data = {
            "profile_id": profile_id,
            "project_id": project_id,
            "name": body.name,
            "target_domain": body.target_domain,
            "user_data_dir": user_data_dir,
            "storage_state_path": "",
            "cdp_port": free,
            "status": "stopped",
            "cdp_endpoint": "",
            "created_at": now,
            "updated_at": now,
            "last_login_at": "",
        }

        profiles = _load_all(project_id)
        profiles.append(data)
        _save_all(project_id, profiles)
        return _to_response(data).model_dump()

    # ── GET /projects/{project_id}/browser-profiles/{profile_id} ──

    @router.get("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def get_profile(request: Request, project_id: str, profile_id: str):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        for d in _load_all(project_id):
            if d["profile_id"] == profile_id:
                return _to_response(d).model_dump()
        return JSONResponse(status_code=404, content={"detail": "Profile not found"})

    # ── PATCH /projects/{project_id}/browser-profiles/{profile_id} ──

    @router.patch("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def update_profile(
        request: Request,
        project_id: str,
        profile_id: str,
        body: UpdateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profiles = _load_all(project_id)
        for d in profiles:
            if d["profile_id"] == profile_id:
                updated = _update_profile_fields(
                    project_id,
                    profile_id,
                    name=body.name if body.name is not None else d["name"],
                    target_domain=(
                        body.target_domain
                        if body.target_domain is not None
                        else d.get("target_domain", "")
                    ),
                )
                if updated is not None:
                    return _to_response(updated).model_dump()
        return JSONResponse(status_code=404, content={"detail": "Profile not found"})

    # ── POST /projects/{project_id}/browser-profiles/{profile_id}/start ──

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/start")
    async def start_profile(
        request: Request,
        project_id: str,
        profile_id: str,
        body: StartBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profile = next((d for d in _load_all(project_id) if d["profile_id"] == profile_id), None)
        if profile is None:
            return JSONResponse(status_code=404, content={"detail": "Profile not found"})

        try:
            endpoint = await asyncio.to_thread(_launch_browser_profile, profile, body.login_url)
        except RuntimeError as exc:
            updated = _update_profile_fields(
                project_id,
                profile_id,
                status="error",
                cdp_endpoint="",
            )
            payload = _to_response(updated or profile).model_dump()
            payload["detail"] = str(exc)
            return JSONResponse(status_code=503, content=payload)

        updated = _update_profile_fields(
            project_id,
            profile_id,
            status="running",
            cdp_endpoint=endpoint,
            cdp_port=profile.get("cdp_port", 0),
        )
        return _to_response(updated or profile).model_dump()

    # ── POST /projects/{project_id}/browser-profiles/{profile_id}/login-complete ──

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/login-complete")
    async def complete_login(
        request: Request,
        project_id: str,
        profile_id: str,
        body: CompleteBrowserProfileLoginRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profile = next((d for d in _load_all(project_id) if d["profile_id"] == profile_id), None)
        if profile is None:
            return JSONResponse(status_code=404, content={"detail": "Profile not found"})

        fields = {"last_login_at": _now_iso()}
        if body.stop_after_save:
            await asyncio.to_thread(_stop_browser_profile, profile_id)
            fields.update({"status": "stopped", "cdp_endpoint": ""})
        updated = _update_profile_fields(project_id, profile_id, **fields)
        return _to_response(updated or profile).model_dump()

    # ── POST /projects/{project_id}/browser-profiles/{profile_id}/stop ──

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/stop")
    async def stop_profile(
        request: Request,
        project_id: str,
        profile_id: str,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profile = next((d for d in _load_all(project_id) if d["profile_id"] == profile_id), None)
        if profile is None:
            return JSONResponse(status_code=404, content={"detail": "Profile not found"})

        await asyncio.to_thread(_stop_browser_profile, profile_id)
        updated = _update_profile_fields(project_id, profile_id, status="stopped", cdp_endpoint="")
        return _to_response(updated or profile).model_dump()

    # ── DELETE /projects/{project_id}/browser-profiles/{profile_id} ──

    @router.delete(
        "/api/v1/projects/{project_id}/browser-profiles/{profile_id}",
        status_code=204,
    )
    async def delete_profile(
        request: Request,
        project_id: str,
        profile_id: str,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await _actor(request)
        if actor is None:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        if not _csrf_ok(request):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            await check_project(project_id)
        except Exception:
            return JSONResponse(status_code=404, content={"detail": "Project not found"})

        profiles = _load_all(project_id)
        new_data = [d for d in profiles if d["profile_id"] != profile_id]
        if len(new_data) == len(profiles):
            return JSONResponse(status_code=404, content={"detail": "Profile not found"})
        await asyncio.to_thread(_stop_browser_profile, profile_id)
        _save_all(project_id, new_data)
        return JSONResponse(status_code=204, content=None)

    return router
