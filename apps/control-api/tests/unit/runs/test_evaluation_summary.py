from agenttest.modules.evaluations.domain import CaseScoreInput, build_evaluation_summary


def test_evaluation_summary_uses_persisted_case_outcomes() -> None:
    summary = build_evaluation_summary(
        [
            CaseScoreInput(run_case_id="a", status="passed"),
            CaseScoreInput(run_case_id="b", status="failed"),
            CaseScoreInput(run_case_id="c", status="error"),
        ]
    )

    assert summary.pass_rate == 1 / 3
    assert summary.aggregate_score == 1 / 3
    assert [item.score for item in summary.scores] == [1.0, 0.0, 0.0]
    assert summary.status == "completed"


def test_evaluation_summary_requires_cases() -> None:
    import pytest

    with pytest.raises(ValueError, match="at least one"):
        build_evaluation_summary([])
