import pandas as pd

from airalert_planner.planner import summarize_trip, summarize_window
from airalert_planner.risk import fit_risk_model


def test_summarize_window_text_contains_disclaimer():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T18:00:00Z"), "weekday": 4, "hour": 18, "alert_active": 1},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T19:00:00Z"), "weekday": 4, "hour": 19, "alert_active": 0},
        ]
    )
    model = fit_risk_model(panel)

    summary = summarize_window(model, "Kyiv", "2026-06-26", 18, 20)

    assert summary.region == "Kyiv"
    assert "official alerts" in summary.to_text()


def test_summarize_window_flags_low_confidence_and_shows_support():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T18:00:00Z"), "weekday": 4, "hour": 18, "alert_active": 1},
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T19:00:00Z"), "weekday": 4, "hour": 19, "alert_active": 0},
        ]
    )
    model = fit_risk_model(panel)

    text = summarize_window(model, "Kyiv", "2026-06-26", 18, 20).to_text()

    assert "Low confidence" in text
    assert "n=" in text  # per-hour support is shown


def test_summarize_window_defines_the_risk_number():
    panel = pd.DataFrame(
        [
            {"region": "Kyiv", "timestamp_hour": pd.Timestamp("2026-06-01T18:00:00Z"), "weekday": 4, "hour": 18, "alert_active": 1},
        ]
    )
    model = fit_risk_model(panel)

    text = summarize_window(model, "Kyiv", "2026-06-26", 18, 19).to_text()

    # The reader must be told what the number means, not just shown a value.
    assert "risk = share" in text


def test_summarize_window_flat_window_reports_no_material_difference():
    # An empty model predicts the same value for every hour -> a flat window.
    model = fit_risk_model(pd.DataFrame(columns=["region", "timestamp_hour", "weekday", "hour", "alert_active"]))

    text = summarize_window(model, "Kyiv", "2026-06-26", 18, 22).to_text()

    assert "No material difference" in text
    assert "Relatively lower-risk hour" not in text


def test_summarize_trip_handles_regions():
    model = fit_risk_model(pd.DataFrame(columns=["region", "timestamp_hour", "weekday", "hour", "alert_active"]))

    text = summarize_trip(model, ["Kyiv", "Lviv"], "2026-06-26")

    assert "Kyiv" in text
    assert "Lviv" in text
    assert "not geospatial routing" in text
