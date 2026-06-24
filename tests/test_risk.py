import pandas as pd

from airalert_planner.risk import chronological_validation, fit_risk_model


def test_risk_model_uses_sparse_fallbacks():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T10:00:00Z"), "weekday": 0, "hour": 10, "alert_active": 1},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-02T10:00:00Z"), "weekday": 1, "hour": 10, "alert_active": 0},
        ]
    )

    model = fit_risk_model(panel)

    assert model.predict_one("Kyiv", 0, 10) == 1.0
    assert model.predict_one("Unknown", 3, 10) == 0.5


def test_chronological_validation_returns_metrics():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp(f"2026-06-0{i}T10:00:00Z"), "weekday": i % 7, "hour": 10, "alert_active": i % 2}
            for i in range(1, 7)
        ]
    )

    metrics = chronological_validation(panel)

    assert metrics["train_rows"] > 0
    assert metrics["test_rows"] > 0
    assert "mae" in metrics
    assert "brier" in metrics
