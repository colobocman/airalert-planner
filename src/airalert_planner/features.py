from __future__ import annotations

import math

import pandas as pd


def build_hourly_panel(events: pd.DataFrame) -> pd.DataFrame:
    """Split alert intervals into hourly region buckets.

    The panel contains only hours touched by alerts in the MVP. A production
    model can later densify the calendar to include explicit zero-alert hours.
    """
    rows: list[dict] = []
    for event in events.itertuples(index=False):
        start = event.started_at
        end = event.ended_at
        current = start.floor("h")
        while current < end:
            bucket_end = current + pd.Timedelta(hours=1)
            overlap_start = max(start, current)
            overlap_end = min(end, bucket_end)
            minutes = max(0.0, (overlap_end - overlap_start).total_seconds() / 60.0)
            if minutes > 0:
                rows.append(
                    {
                        "region": event.region,
                        "timestamp_hour": current,
                        "alert_active": 1,
                        "alert_count": 1,
                        "alert_minutes": minutes,
                    }
                )
            current = bucket_end

    if not rows:
        return pd.DataFrame(
            columns=[
                "region",
                "timestamp_hour",
                "alert_active",
                "alert_count",
                "alert_minutes",
                "hour",
                "weekday",
                "is_night",
            ]
        )

    panel = pd.DataFrame(rows)
    active = (
        panel.groupby(["region", "timestamp_hour"], as_index=False)
        .agg(alert_active=("alert_active", "max"), alert_count=("alert_count", "sum"), alert_minutes=("alert_minutes", "sum"))
        .sort_values(["region", "timestamp_hour"])
    )

    # Densify each regional series so the baseline learns from both alert and
    # non-alert hours. Without explicit zero hours, every observed bucket would
    # be alert-active and risk would trivially become 1.0 everywhere.
    dense_parts: list[pd.DataFrame] = []
    for region, region_events in events.groupby("region"):
        start = region_events["started_at"].min().floor("h")
        end = region_events["ended_at"].max().ceil("h")
        hours = pd.date_range(start=start, end=end - pd.Timedelta(hours=1), freq="h")
        dense_parts.append(pd.DataFrame({"region": region, "timestamp_hour": hours}))
    dense = pd.concat(dense_parts, ignore_index=True)
    panel = dense.merge(active, on=["region", "timestamp_hour"], how="left")
    panel["alert_active"] = panel["alert_active"].fillna(0).astype(int)
    panel["alert_count"] = panel["alert_count"].fillna(0).astype(int)
    panel["alert_minutes"] = panel["alert_minutes"].fillna(0.0)

    panel["hour"] = panel["timestamp_hour"].dt.hour
    panel["weekday"] = panel["timestamp_hour"].dt.weekday
    panel["is_night"] = panel["hour"].map(lambda h: h >= 22 or h < 6)
    panel["alert_minutes"] = panel["alert_minutes"].map(lambda value: round(float(value), 3) if not math.isnan(value) else value)
    return panel.reset_index(drop=True)
