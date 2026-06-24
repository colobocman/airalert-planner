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


def test_summarize_trip_handles_regions():
    model = fit_risk_model(pd.DataFrame(columns=["region", "timestamp_hour", "weekday", "hour", "alert_active"]))

    text = summarize_trip(model, ["Kyiv", "Lviv"], "2026-06-26")

    assert "Kyiv" in text
    assert "Lviv" in text
    assert "not geospatial routing" in text
