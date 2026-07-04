"""Browser Profile 注册表。

维护浏览器实例的 CRUD，每个 Profile 对应：
- 独立 Chrome user-data-dir（完整浏览器状态）
- storageState JSON 文件（cookies + localStorage）
- 专属 CDP 调试端口

参照 Browserless Authenticated Profiles 和 Browser-use Profiles 的设计模式。
"""

from __future__ import annotations

import json
import socket
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class BrowserProfile:
    """浏览器实例配置。"""

    profile_id: str  # UUID
    project_id: str  # 项目隔离
    name: str  # 人类可读名称（如"公司内网-管理员"）
    target_domain: str  # 目标网站域名
    user_data_dir: str  # Chrome --user-data-dir 路径
    storage_state_path: str  # storageState JSON 路径（空=未登录）
    cdp_port: int  # CDP 调试端口（自动分配）
    status: str  # "stopped" | "running" | "error"
    cdp_endpoint: str  # 运行时的 CDP WebSocket URL
    created_at: str = ""
    updated_at: str = ""


# ── 存储路径 ──────────────────────────────────────────


def _registry_root() -> Path:
    return Path.home() / ".agenttest" / "browser-profiles"


def _registry_path(project_id: str) -> Path:
    root = _registry_root()
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{project_id}.json"


# ── 默认存储目录 ──────────────────────────────────────


def _default_profile_dir(profile_id: str) -> str:
    root = _registry_root()
    return str(root / "data" / profile_id)


# ── 端口分配 ──────────────────────────────────────────


def _find_free_port(start: int = 9222) -> int:
    """从 start 起扫描，返回首个空闲 TCP 端口。"""
    port = start
    while port < start + 1000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"无法在 [{start}, {start + 1000}) 范围内找到空闲端口")


def _used_ports(project_id: str) -> set[int]:
    """当前 project 已分配的端口集合。"""
    try:
        profiles = list_profiles(project_id)
        return {p.cdp_port for p in profiles}
    except Exception:
        return set()


# ── 辅助 ──────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _serialize(profile: BrowserProfile) -> dict:
    return {
        "profile_id": profile.profile_id,
        "project_id": profile.project_id,
        "name": profile.name,
        "target_domain": profile.target_domain,
        "user_data_dir": profile.user_data_dir,
        "storage_state_path": profile.storage_state_path,
        "cdp_port": profile.cdp_port,
        "status": profile.status,
        "cdp_endpoint": profile.cdp_endpoint,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def _deserialize(data: dict) -> BrowserProfile:
    return BrowserProfile(
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


# ── CRUD ──────────────────────────────────────────────


def create_profile(
    project_id: str,
    name: str,
    *,
    target_domain: str = "",
    user_data_dir: str = "",
) -> BrowserProfile:
    """创建新的浏览器实例配置。

    Args:
        project_id: 所属项目
        name: 人类可读名称
        target_domain: 目标域名
        user_data_dir: 自定义 Chrome 数据目录（空则自动生成）
    """
    profile_id = str(uuid.uuid4())
    if not user_data_dir:
        user_data_dir = _default_profile_dir(profile_id)

    # 确保 user_data_dir 的父目录存在
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)

    # 分配端口（跳过已占用的）
    used = _used_ports(project_id)
    free = _find_free_port(9222)
    while free in used:
        free = _find_free_port(free + 1)

    now = _now_iso()
    profile = BrowserProfile(
        profile_id=profile_id,
        project_id=project_id,
        name=name,
        target_domain=target_domain,
        user_data_dir=user_data_dir,
        storage_state_path="",
        cdp_port=free,
        status="stopped",
        cdp_endpoint="",
        created_at=now,
        updated_at=now,
    )

    profiles = _load_all(project_id)
    profiles.append(_serialize(profile))
    _save_all(project_id, profiles)
    return profile


def list_profiles(project_id: str) -> list[BrowserProfile]:
    """列出项目下所有浏览器实例。"""
    return [_deserialize(d) for d in _load_all(project_id)]


def get_profile(project_id: str, profile_id: str) -> BrowserProfile | None:
    """获取单个浏览器实例。

    若 project_id 为空，遍历所有项目文件查找（性能较低，适用于
    只知道 profile_id 的场景）。
    """
    if project_id:
        for profile in list_profiles(project_id):
            if profile.profile_id == profile_id:
                return profile
        return None
    # 无 project_id：遍历所有
    registry_root = _registry_root()
    if not registry_root.is_dir():
        return None
    for f in registry_root.glob("*.json"):
        pid = f.stem
        for profile in list_profiles(pid):
            if profile.profile_id == profile_id:
                return profile
    return None


def update_profile(
    project_id: str,
    profile_id: str,
    **kwargs,
) -> BrowserProfile | None:
    """更新浏览器实例的字段。

    支持更新: name, target_domain, storage_state_path, status, cdp_endpoint。
    """
    profiles_data = _load_all(project_id)
    for data in profiles_data:
        if data["profile_id"] == profile_id:
            allowed = {
                "name",
                "target_domain",
                "storage_state_path",
                "status",
                "cdp_endpoint",
            }
            for k, v in kwargs.items():
                if k in allowed:
                    data[k] = v
            data["updated_at"] = _now_iso()
            _save_all(project_id, profiles_data)
            return _deserialize(data)
    return None


def delete_profile(project_id: str, profile_id: str) -> bool:
    """删除浏览器实例配置（不删除 user-data-dir 以保留数据）。"""
    profiles_data = _load_all(project_id)
    new_data = [d for d in profiles_data if d["profile_id"] != profile_id]
    if len(new_data) == len(profiles_data):
        return False  # 未找到
    _save_all(project_id, new_data)
    return True


# ── 内部存储 I/O ──────────────────────────────────────


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
