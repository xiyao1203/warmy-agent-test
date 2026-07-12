from agenttest.modules.scorers.domain.calibration import CalibrationMetrics


def test_calibration_metrics_measure_false_results() -> None:
    metrics = CalibrationMetrics.from_labels(
        predicted=(True, True, False, False), actual=(True, False, True, False)
    )
    assert metrics.accuracy == 0.5
    assert metrics.false_positive_rate == 0.5
    assert metrics.false_negative_rate == 0.5
    assert metrics.calibrated is False
