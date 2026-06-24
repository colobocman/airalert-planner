import pandas as pd
import pytest

from airalert_planner.risk import (
    _rolling_folds,
    chronological_validation,
    fit_risk_model,
    risk_table,
)


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


def _rolling_panel() -> pd.DataFrame:
    """16 contiguous hourly rows in time order for rolling-origin validation."""
    return pd.DataFrame(
        [
            {
                "region": "Kyiv",
                "timestamp_hour": pd.Timestamp("2026-06-01T00:00:00Z") + pd.Timedelta(hours=i),
                "weekday": 0,
                "hour": i % 24,
                "alert_active": i % 2,
            }
            for i in range(16)
        ]
    )


def _signal_panel() -> pd.DataFrame:
    """Hour 6 always alerts, hour 18 never does, over 24 days, one region.

    A stable, learnable signal so the frequency model beats the base rate and
    brier_lift is meaningfully positive -- not a 0 == 0 identity that would pass
    even if the lift sign were reversed.
    """
    base = pd.Timestamp("2026-06-01T00:00:00Z")
    rows = []
    for day in range(24):
        for hour, active in ((6, 1), (18, 0)):
            ts = base + pd.Timedelta(days=day, hours=hour)
            rows.append(
                {"region": "Kyiv", "timestamp_hour": ts, "weekday": ts.weekday(), "hour": hour, "alert_active": active}
            )
    return pd.DataFrame(rows)


def _multi_region_panel() -> pd.DataFrame:
    """Three regions sharing every timestamp -- exercises the interleaving path."""
    base = pd.Timestamp("2026-06-01T00:00:00Z")
    rows = []
    for i in range(20):
        ts = base + pd.Timedelta(hours=i)
        for offset, region in enumerate(("Kyiv", "Lviv", "Kharkiv")):
            rows.append(
                {"region": region, "timestamp_hour": ts, "weekday": ts.weekday(), "hour": i % 24, "alert_active": (i + offset) % 2}
            )
    return pd.DataFrame(rows)


def test_chronological_validation_uses_rolling_origin_folds():
    metrics = chronological_validation(_rolling_panel())

    # Rolling-origin validation evaluates several expanding-window folds, not a
    # single 80/20 split, so the estimate is not hostage to one cut point.
    assert metrics["n_splits"] >= 2
    assert len(metrics["folds"]) == metrics["n_splits"]
    assert all("brier" in fold for fold in metrics["folds"])


def test_rolling_folds_split_on_whole_timestamps():
    # Many regions share each timestamp. Folds must split on whole timestamps so
    # no test hour can inform its own training data through the shared
    # global-hour table -- and train must always precede test in time.
    ordered = _multi_region_panel().sort_values("timestamp_hour").reset_index(drop=True)

    folds = list(_rolling_folds(ordered, 3))

    assert len(folds) == 3
    for train, test in folds:
        train_ts = set(train["timestamp_hour"])
        test_ts = set(test["timestamp_hour"])
        assert train_ts.isdisjoint(test_ts)
        assert max(train_ts) < min(test_ts)


def test_chronological_validation_reports_brier_lift():
    metrics = chronological_validation(_signal_panel())

    # Lift is the headline number: baseline Brier minus model Brier. The signal
    # panel makes the model genuinely better, so a reversed sign would fail here.
    assert metrics["brier_lift"] == pytest.approx(metrics["baseline_brier"] - metrics["brier"])
    assert metrics["brier_lift"] > 0.0


def _seasonal_panel() -> pd.DataFrame:
    """One region; hour 6 active 75% of days, hour 18 active 25% -- a real
    hour-of-day signal that is informative but far from perfect, with no
    region/weekday signal for the model to exploit beyond the daily cycle."""
    base = pd.Timestamp("2026-06-01T00:00:00Z")
    rows = []
    for day in range(24):
        ts6 = base + pd.Timedelta(days=day, hours=6)
        ts18 = base + pd.Timedelta(days=day, hours=18)
        rows.append({"region": "Kyiv", "timestamp_hour": ts6, "weekday": ts6.weekday(), "hour": 6, "alert_active": 1 if day % 4 != 0 else 0})
        rows.append({"region": "Kyiv", "timestamp_hour": ts18, "weekday": ts18.weekday(), "hour": 18, "alert_active": 1 if day % 4 == 0 else 0})
    return pd.DataFrame(rows)


def test_chronological_validation_reports_hour_of_day_climatology():
    metrics = chronological_validation(_seasonal_panel())

    # The hour-of-day climatology is a stronger (lower-Brier) bar than a constant
    # base-rate predictor, because it captures the daily cycle the model relies on.
    assert "climatology_brier" in metrics
    assert "climatology_mae" in metrics
    assert metrics["climatology_brier"] < metrics["baseline_brier"]


def test_chronological_validation_reports_brier_skill_score():
    metrics = chronological_validation(_seasonal_panel())

    # Skill score normalizes model Brier against the climatology bar:
    # 1 - model/climatology (0 = no skill beyond the daily cycle, 1 = perfect).
    assert metrics["brier_skill_score"] == pytest.approx(1 - metrics["brier"] / metrics["climatology_brier"])


def test_chronological_validation_insufficient_below_two_splits():
    # n_splits=1 cannot make a rolling-origin fold; return the sentinel instead
    # of letting TimeSeriesSplit raise. The sentinel must carry the same keys as
    # the success path so callers never hit a KeyError on brier_lift.
    metrics = chronological_validation(_signal_panel(), n_splits=1)

    assert metrics["n_splits"] == 0
    assert metrics["test_rows"] == 0.0
    assert metrics["brier_lift"] == 0.0
    assert "folds" in metrics


def test_chronological_validation_allows_three_timestamps():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp(f"2026-06-0{i}T10:00:00Z"), "weekday": 0, "hour": 10, "alert_active": i % 2}
            for i in range(1, 4)
        ]
    )

    # Three distinct timestamps support two expanding-window folds; the old
    # len < 4 guard wrongly rejected this.
    metrics = chronological_validation(panel)

    assert metrics["n_splits"] == 2


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
