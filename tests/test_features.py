import pandas as pd

from airalert_planner.features import build_hourly_panel


def test_build_hourly_panel_splits_midnight_alert():
    events = pd.DataFrame(
        [
            {
                "region": "Kyiv",
                "started_at": pd.Timestamp("2026-06-01T23:30:00+03:00").tz_convert("UTC"),
                "ended_at": pd.Timestamp("2026-06-02T00:30:00+03:00").tz_convert("UTC"),
                "duration_minutes": 60,
            }
        ]
    )

    panel = build_hourly_panel(events)

    assert len(panel) == 2
    assert panel["alert_minutes"].tolist() == [30.0, 30.0]
    assert panel["alert_active"].tolist() == [1, 1]
