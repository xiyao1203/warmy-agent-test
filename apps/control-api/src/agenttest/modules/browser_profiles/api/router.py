"""Browser Profile CRUD API。

提供浏览器实例的增删改查 HTTP 端点，存储与插件层
profile_registry.py 共享同一套 JSON 文件。
"""

from __future__ import annotations

import json
import socket
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

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
    )


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
                if body.name is not None:
                    d["name"] = body.name
                if body.target_domain is not None:
                    d["target_domain"] = body.target_domain
                d["updated_at"] = _now_iso()
                _save_all(project_id, profiles)
                return _to_response(d).model_dump()
        return JSONResponse(status_code=404, content={"detail": "Profile not found"})

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
        _save_all(project_id, new_data)
        return JSONResponse(status_code=204, content=None)

    return router
