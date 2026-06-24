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


def test_panel_hour_and_weekday_use_local_timezone():
    # 19:05-19:55 Kyiv local == 16:05-16:55 UTC. The hour a user asks about is
    # local time, so the panel must read hour 19 (not the UTC 16) and weekday 1
    # (Tuesday 2026-06-02 in Kyiv).
    events = pd.DataFrame(
        [
            {
                "region": "Kyiv",
                "started_at": pd.Timestamp("2026-06-02T16:05:00Z"),
                "ended_at": pd.Timestamp("2026-06-02T16:55:00Z"),
                "duration_minutes": 50,
            }
        ]
    )

    panel = build_hourly_panel(events)

    assert panel["hour"].tolist() == [19]
    assert panel["weekday"].tolist() == [1]


def test_build_hourly_panel_inserts_zero_hours_between_alerts():
    # Two alerts 3 hours apart in one region: the gap hours must appear as
    # explicit zero-alert rows, otherwise every observed hour is alert-active
    # and risk trivially becomes 1.0.
    events = pd.DataFrame(
        [
            {
                "region": "Kyiv",
                "started_at": pd.Timestamp("2026-06-01T00:05:00Z"),
                "ended_at": pd.Timestamp("2026-06-01T00:25:00Z"),
                "duration_minutes": 20,
            },
            {
                "region": "Kyiv",
                "started_at": pd.Timestamp("2026-06-01T03:05:00Z"),
                "ended_at": pd.Timestamp("2026-06-01T03:25:00Z"),
                "duration_minutes": 20,
            },
        ]
    )

    panel = build_hourly_panel(events)

    assert (panel["alert_active"] == 1).sum() == 2
    assert (panel["alert_active"] == 0).any()
