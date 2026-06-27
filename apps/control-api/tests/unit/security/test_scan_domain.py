"""Unit tests for SecurityScan domain entity."""

from __future__ import annotations

from uuid import uuid4

from agenttest.modules.security.domain.models import (
    FindingCategory,
    ScanStatus,
    SecurityScan,
)


def test_scan_create() -> None:
    s = SecurityScan.create(project_id=uuid4())
    assert s.status is ScanStatus.PENDING
    assert s.scan_type == "full"
    assert s.findings == []
    assert s.summary == {}
    assert s.completed_at is None


def test_scan_create_custom_type() -> None:
    s = SecurityScan.create(project_id=uuid4(), scan_type="quick")
    assert s.scan_type == "quick"


def test_scan_complete() -> None:
    s = SecurityScan.create(project_id=uuid4())
    findings = [
        {"category": "injection", "severity": "high"},
        {"category": "injection", "severity": "medium"},
        {"category": "leak", "severity": "low"},
    ]
    s.complete(findings)
    assert s.status is ScanStatus.COMPLETED
    assert s.completed_at is not None
    assert s.summary == {"injection": 2, "leak": 1}


def test_scan_complete_empty() -> None:
    s = SecurityScan.create(project_id=uuid4())
    s.complete([])
    assert s.status is ScanStatus.COMPLETED
    assert s.summary == {}


def test_scan_fail() -> None:
    s = SecurityScan.create(project_id=uuid4())
    s.fail("Connection timeout")
    assert s.status is ScanStatus.FAILED


def test_scan_status_values() -> None:
    assert ScanStatus.PENDING == "pending"
    assert ScanStatus.RUNNING == "running"
    assert ScanStatus.COMPLETED == "completed"
    assert ScanStatus.FAILED == "failed"


def test_finding_category_values() -> None:
    assert FindingCategory.INJECTION == "injection"
    assert FindingCategory.LEAK == "leak"
    assert FindingCategory.JAILBREAK == "jailbreak"
    assert FindingCategory.OTHER == "other"
