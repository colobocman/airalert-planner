import pandas as pd
import pytest

from airalert_planner.risk import chronological_validation, fit_risk_model, risk_table


def _kyiv_hour18_panel() -> pd.DataFrame:
    """Kyiv at hour 18: alert-active on weekdays 0 and 1, quiet on 2 and 4.

    The region+hour alert rate is therefore 0.5, while each individual
    (weekday, hour) cell is backed by a single observation.
    """
    return pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T18:00:00Z"), "weekday": 0, "hour": 18, "alert_active": 1},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-02T18:00:00Z"), "weekday": 1, "hour": 18, "alert_active": 1},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-03T18:00:00Z"), "weekday": 2, "hour": 18, "alert_active": 0},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-05T18:00:00Z"), "weekday": 4, "hour": 18, "alert_active": 0},
        ]
    )


def test_thin_zero_leaf_shrinks_up_toward_parent():
    model = fit_risk_model(_kyiv_hour18_panel())

    # The (weekday 4, hour 18) cell is a single 0 observation. Without shrinkage
    # it reports a confident 0.00; with shrinkage it is pulled toward the 0.5
    # region+hour rate but stays below it.
    estimate = model.predict_one("Kyiv", 4, 18)

    assert 0.0 < estimate < 0.5


def test_thin_one_leaf_shrinks_down_toward_parent():
    model = fit_risk_model(_kyiv_hour18_panel())

    # The (weekday 0, hour 18) cell is a single 1 observation. Shrinkage pulls
    # it down from a confident 1.00 toward the 0.5 region+hour rate.
    estimate = model.predict_one("Kyiv", 0, 18)

    assert 0.5 < estimate < 1.0


def test_unknown_region_falls_back_to_global_mean():
    model = fit_risk_model(_kyiv_hour18_panel())

    # No region or hour evidence at all -> fall back to the global mean.
    assert model.predict_one("Atlantis", 3, 9) == pytest.approx(model.global_mean)


def test_risk_table_rounds_for_stable_output():
    model = fit_risk_model(_kyiv_hour18_panel())

    table = risk_table(model, ["Kyiv"])

    # Risk is rounded so regenerated regional_risk.csv diffs cleanly across runs.
    assert (table["risk"] == table["risk"].round(4)).all()


def test_support_one_counts_backing_observations():
    model = fit_risk_model(_kyiv_hour18_panel())

    # (Kyiv, weekday 0, hour 18) is backed by a single observation.
    assert model.support_one("Kyiv", 0, 18) == 1
    # No region/hour evidence -> zero support.
    assert model.support_one("Atlantis", 0, 3) == 0


def test_support_one_reflects_only_the_exact_slot():
    model = fit_risk_model(_kyiv_hour18_panel())

    # Hour 18 has region history, but weekday 6 at hour 18 was never observed.
    # Support must be 0 (not the region+hour count) so the low-confidence guard
    # fires: the estimate for this slot is borrowed from broader history.
    assert model.support_one("Kyiv", 6, 18) == 0


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


def test_chronological_validation_reports_base_rate_baseline():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp(f"2026-06-0{i}T10:00:00Z"), "weekday": i % 7, "hour": 10, "alert_active": i % 2}
            for i in range(1, 7)
        ]
    )

    metrics = chronological_validation(panel)

    # A constant base-rate predictor must be reported alongside the model so a
    # low score on a rare positive class can't masquerade as skill.
    assert "baseline_mae" in metrics
    assert "baseline_brier" in metrics
    assert metrics["baseline_brier"] >= 0.0
