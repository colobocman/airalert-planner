from __future__ import annotations

import pandas as pd


def summarize_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["region", "alerts", "median_duration_minutes", "mean_duration_minutes"])
    return (
        events.groupby("region", as_index=False)
        .agg(
            alerts=("region", "size"),
            median_duration_minutes=("duration_minutes", "median"),
            mean_duration_minutes=("duration_minutes", "mean"),
        )
        .sort_values(["alerts", "median_duration_minutes"], ascending=False)
    )
