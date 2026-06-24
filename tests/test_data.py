from pathlib import Path

import pytest

from airalert_planner.data import load_alert_events


def test_load_alert_events_computes_duration(tmp_path: Path):
    path = tmp_path / "alerts.csv"
    path.write_text("region,started_at,ended_at\nKyiv,2026-06-01T01:00:00+03:00,2026-06-01T02:30:00+03:00\n")

    result = load_alert_events(path)

    assert len(result.events) == 1
    assert result.events.loc[0, "region"] == "Kyiv"
    assert result.events.loc[0, "duration_minutes"] == 90
    assert result.invalid_rows.empty


def test_load_alert_events_separates_invalid_rows(tmp_path: Path):
    path = tmp_path / "alerts.csv"
    path.write_text("region,started_at,ended_at\nKyiv,2026-06-01T02:00:00+03:00,2026-06-01T01:00:00+03:00\n")

    result = load_alert_events(path)

    assert result.events.empty
    assert len(result.invalid_rows) == 1


def test_load_alert_events_requires_columns(tmp_path: Path):
    path = tmp_path / "alerts.csv"
    path.write_text("region,started_at\nKyiv,2026-06-01T01:00:00+03:00\n")

    with pytest.raises(ValueError):
        load_alert_events(path)
