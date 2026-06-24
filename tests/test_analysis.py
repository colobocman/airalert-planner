import pandas as pd

from airalert_planner.analysis import summarize_events


def test_summarize_events_rounds_durations():
    events = pd.DataFrame(
        [
            {"region": "Kyiv", "duration_minutes": 47.0},
            {"region": "Kyiv", "duration_minutes": 50.0},
            {"region": "Kyiv", "duration_minutes": 52.0},
        ]
    )

    summary = summarize_events(events)

    # Durations are rounded so regenerated summary.csv diffs cleanly.
    mean = summary.iloc[0]["mean_duration_minutes"]
    assert mean == round(mean, 2)


def test_summarize_events_orders_ties_by_region():
    events = pd.DataFrame(
        [
            {"region": "Lviv", "duration_minutes": 30.0},
            {"region": "Kyiv", "duration_minutes": 30.0},
        ]
    )

    summary = summarize_events(events)

    # Equal alert counts and medians -> deterministic region tiebreak.
    assert summary["region"].tolist() == ["Kyiv", "Lviv"]
