"""验证安全扫描与安全策略的领域模型和数据契约。

覆盖：
- SecurityScan 实体生命周期（create/complete/fail）
- PolicyEngine 策略评估逻辑
- SecurityPolicy 模型约束
- 安全扫描项目隔离
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest.modules.security.domain.models import (
    PolicyEngine,
    ScanStatus,
    SecurityPolicy,
    SecurityScan,
)
from agenttest.modules.security.infrastructure.repositories import (
    SecurityScanModel,
)

# ── SecurityScan 实体测试 ─────────────────────────────────────────────


def test_security_scan_starts_as_pending() -> None:
    """新创建的安全扫描状态为 pending。"""
    scan = SecurityScan.create(
        project_id=uuid4(),
    )

    assert scan.status is ScanStatus.PENDING
    assert scan.findings == []
    assert scan.summary == {}
    assert scan.completed_at is None


def test_security_scan_with_asset_references() -> None:
    """安全扫描可以关联 Agent、Environment、SecurityProfile 和 Run。"""
    agent_id = uuid4()
    env_id = uuid4()
    profile_id = uuid4()
    run_id = uuid4()

    scan = SecurityScan.create(
        project_id=uuid4(),
        scan_type="prompt_injection",
        run_id=run_id,
        agent_version_id=agent_id,
        environment_version_id=env_id,
        security_profile_id=profile_id,
    )

    assert scan.run_id == run_id
    assert scan.agent_version_id == agent_id
    assert scan.environment_version_id == env_id
    assert scan.security_profile_id == profile_id


def test_security_scan_complete_calculates_summary() -> None:
    """安全扫描完成时正确统计分类并计算评分。"""
    scan = SecurityScan.create(project_id=uuid4())

    findings = [
        {"category": "injection", "score": 0.8, "description": "SQL injection"},
        {"category": "injection", "score": 0.5, "description": "XSS"},
        {"category": "leak", "score": 0.2, "description": "API key leak"},
    ]
    scan.complete(findings)

    assert scan.status is ScanStatus.COMPLETED
    assert scan.summary["injection"] == 2
    assert scan.summary["leak"] == 1
    assert scan.summary["score"] == pytest.approx((0.8 + 0.5 + 0.2) / 3)
    assert scan.completed_at is not None


def test_security_scan_complete_handles_empty_findings() -> None:
    """无发现时评分为满分 1.0。"""
    scan = SecurityScan.create(project_id=uuid4())

    scan.complete([])

    assert scan.status is ScanStatus.COMPLETED
    assert scan.summary["score"] == 1.0


def test_security_scan_fail_records_error() -> None:
    """安全扫描失败时记录错误。"""
    scan = SecurityScan.create(project_id=uuid4())

    scan.fail("Promptfoo process crashed")

    assert scan.status is ScanStatus.FAILED
    assert scan.summary == {"error": 1}


# ── PolicyEngine 测试 ──────────────────────────────────────────────────


def test_policy_engine_checks_step_limit() -> None:
    """策略引擎检查步骤数限制。"""
    policy = SecurityPolicy(
        id=uuid4(),
        project_id=uuid4(),
        name="strict",
        max_steps=10,
        enabled=True,
    )
    engine = PolicyEngine(policy)

    assert engine.check_step_limit(5) is True
    assert engine.check_step_limit(10) is True
    assert engine.check_step_limit(11) is False


def test_policy_engine_checks_timeout() -> None:
    """策略引擎检查超时限制。"""
    policy = SecurityPolicy(
        id=uuid4(),
        project_id=uuid4(),
        name="strict",
        timeout_seconds=300,
        enabled=True,
    )
    engine = PolicyEngine(policy)

    assert engine.check_timeout(100) is True
    assert engine.check_timeout(300) is True
    assert engine.check_timeout(301) is False


def test_policy_engine_blocks_listed_tools() -> None:
    """策略引擎阻止黑名单中的工具。"""
    policy = SecurityPolicy(
        id=uuid4(),
        project_id=uuid4(),
        name="block-tools",
        blocked_tools=["eval", "exec", "os.system"],
        enabled=True,
    )
    engine = PolicyEngine(policy)

    assert engine.is_tool_blocked("eval") is True
    assert engine.is_tool_blocked("os.system") is True
    assert engine.is_tool_blocked("read_file") is False


def test_policy_engine_disabled_policy_allows_all() -> None:
    """禁用策略时所有操作通过。"""
    engine = PolicyEngine(None)

    assert engine.check_step_limit(999) is True
    assert engine.check_timeout(9999) is True
    assert engine.is_tool_blocked("eval") is False
    assert engine.needs_confirmation("eval") is False


def test_policy_engine_confirmation_only_for_blocked_tools() -> None:
    """只有黑名单工具才需要确认。"""
    policy = SecurityPolicy(
        id=uuid4(),
        project_id=uuid4(),
        name="confirm",
        blocked_tools=["dangerous_tool"],
        require_confirmation=True,
        enabled=True,
    )
    engine = PolicyEngine(policy)

    assert engine.needs_confirmation("dangerous_tool") is True
    assert engine.needs_confirmation("safe_tool") is False


# ── 持久化模型约束测试 ────────────────────────────────────────────────


def test_security_scan_model_has_project_foreign_key() -> None:
    """安全扫描表强制项目外键。"""
    fk_columns = {fk.parent.name for fk in SecurityScanModel.__table__.foreign_keys}
    assert "project_id" in fk_columns


def test_security_scan_model_has_asset_reference_columns() -> None:
    """安全扫描模型包含资产引用列。"""
    columns = {c.name: c for c in SecurityScanModel.__table__.c}
    for col in ("run_id", "agent_version_id", "environment_version_id", "security_profile_id"):
        assert col in columns, f"SecurityScanModel missing column: {col}"
