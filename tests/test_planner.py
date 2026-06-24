import pandas as pd
import pytest

from airalert_planner.planner import risk_band, summarize_trip, summarize_window
from airalert_planner.risk import fit_risk_model


def _contrast_model():
    """Kyiv hour 18 almost always active, hour 19 almost never -- a high and a
    low hour with enough history to avoid the low-confidence flag."""
    rows = []
    base = pd.Timestamp("2026-06-01T00:00:00Z")
    for day in range(28):
        ts18 = base + pd.Timedelta(days=day, hours=18)
        ts19 = base + pd.Timedelta(days=day, hours=19)
        rows.append({"region": "Kyiv", "timestamp_hour": ts18, "weekday": ts18.weekday(), "hour": 18, "alert_active": 1})
        rows.append({"region": "Kyiv", "timestamp_hour": ts19, "weekday": ts19.weekday(), "hour": 19, "alert_active": 0})
    return fit_risk_model(pd.DataFrame(rows))


@pytest.mark.parametrize(
    "risk,band",
    [
        (0.0, "Low"),
        (0.05, "Low"),
        (0.099, "Low"),
        (0.10, "Medium"),
        (0.25, "Medium"),
        (0.299, "Medium"),
        (0.30, "High"),
        (0.74, "High"),
        (1.0, "High"),
    ],
)
def test_risk_band_thresholds(risk, band):
    assert risk_band(risk) == band


def test_summarize_window_explains_risk_bands():
    text = summarize_window(_contrast_model(), "Kyiv", "2026-06-26", 18, 20).to_text()
    lower = text.lower()

    # A planner must be told what Low/Medium/High mean and where the cutoffs are.
    assert "risk bands" in lower
    assert "low" in lower and "medium" in lower and "high" in lower
    assert "0.10" in text and "0.30" in text


def test_summarize_window_labels_average_and_hours_with_bands():
    text = summarize_window(_contrast_model(), "Kyiv", "2026-06-26", 18, 20).to_text()
    lines = text.splitlines()

    avg_line = next(line for line in lines if line.startswith("Average historical risk"))
    assert any(band in avg_line for band in ("Low", "Medium", "High"))

    high_hour = next(line for line in lines if line.startswith("- 18:00"))
    low_hour = next(line for line in lines if line.startswith("- 19:00"))
    assert "High" in high_hour
    assert "Low" in low_hour


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
