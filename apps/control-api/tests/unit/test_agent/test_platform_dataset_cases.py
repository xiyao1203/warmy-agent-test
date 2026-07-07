import pytest
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.test_agent.adapters.platform import _test_case_command_from_raw
from agenttest.modules.test_agent.application.platform_catalog import DatasetWithCasesInput
from pydantic import ValidationError


def test_dataset_case_input_accepts_platform_standard_fields() -> None:
    payload = DatasetWithCasesInput.model_validate(
        {
            "name": "Agent 生成数据集",
            "cases": [
                {
                    "name": "完整字段用例",
                    "input": {"message": "hello"},
                    "execution_mode": "api",
                    "initial_state": {"user_tier": "free"},
                    "expected_outcome": {"contains": "hello"},
                    "assertions": [{"type": "contains", "value": "hello"}],
                    "scorers": [{"type": "llm_judge", "threshold": 0.8}],
                    "security_policies": [{"type": "pii_redaction"}],
                    "tags": ["agent", "smoke"],
                    "scenario": "基础问候",
                    "priority": "P1",
                    "risk_level": "low",
                    "difficulty": "easy",
                    "test_group": "test",
                }
            ],
        }
    )

    case = payload.cases[0]
    assert case.expected_outcome == {"contains": "hello"}
    assert case.security_policies == [{"type": "pii_redaction"}]
    assert case.priority == "P1"
    assert case.test_group == "test"


def test_dataset_case_input_accepts_codex_browser_mode() -> None:
    payload = DatasetWithCasesInput.model_validate(
        {
            "name": "Codex 浏览器探索集",
            "cases": [
                {
                    "name": "画布自动探索",
                    "input": {
                        "url": "https://example.test/canvas",
                        "test_intent": "打开画布并确认主流程可用",
                        "timeout": 120,
                    },
                    "execution_mode": "codex_explore",
                }
            ],
        }
    )

    assert payload.cases[0].execution_mode == "codex_explore"


def test_dataset_case_input_rejects_unknown_enums() -> None:
    with pytest.raises(ValidationError):
        DatasetWithCasesInput.model_validate(
            {
                "name": "bad",
                "cases": [
                    {
                        "name": "bad enum",
                        "input": {"message": "hello"},
                        "execution_mode": "canvas",
                        "priority": "P99",
                        "risk_level": "extreme",
                        "test_group": "production",
                    }
                ],
            }
        )


def test_agent_case_raw_payload_maps_to_full_dataset_command() -> None:
    command = _test_case_command_from_raw(
        dataset_version_id=DatasetVersionId.new(),
        raw={
            "name": "Agent 同步用例",
            "input": {"message": "hello"},
            "execution_mode": "api",
            "initial_state": {"locale": "zh-CN"},
            "expected_outcome": {"contains": "hello"},
            "assertions": [{"type": "contains", "value": "hello"}],
            "scorers": [{"type": "llm_judge", "threshold": 0.8}],
            "security_policies": [{"type": "pii_redaction"}],
            "tags": ["agent", "sync"],
            "scenario": "基础问候",
            "priority": "P0",
            "risk_level": "critical",
            "difficulty": "medium",
            "test_group": "validation",
        },
        fallback_name="Fallback",
        fallback_input=None,
        default_execution_mode="api",
    )

    assert command.name == "Agent 同步用例"
    assert command.input == {"message": "hello"}
    assert command.initial_state == {"locale": "zh-CN"}
    assert command.expected_outcome == {"contains": "hello"}
    assert command.security_policies == [{"type": "pii_redaction"}]
    assert command.tags == ["agent", "sync"]
    assert command.scenario == "基础问候"
    assert command.priority and command.priority.value == "P0"
    assert command.risk_level and command.risk_level.value == "critical"
    assert command.difficulty == "medium"
    assert command.test_group and command.test_group.value == "validation"
