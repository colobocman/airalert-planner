from __future__ import annotations

import pandas as pd


def summarize_events(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["region", "alerts", "median_duration_minutes", "mean_duration_minutes"])
    summary = events.groupby("region", as_index=False).agg(
        alerts=("region", "size"),
        median_duration_minutes=("duration_minutes", "median"),
        mean_duration_minutes=("duration_minutes", "mean"),
    )
    # Round for stable summary.csv diffs; region tiebreak makes ordering deterministic.
    summary["median_duration_minutes"] = summary["median_duration_minutes"].round(2)
    summary["mean_duration_minutes"] = summary["mean_duration_minutes"].round(2)
    return summary.sort_values(
        ["alerts", "median_duration_minutes", "region"], ascending=[False, False, True]
    ).reset_index(drop=True)
