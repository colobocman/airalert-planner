from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"region", "started_at", "ended_at"}


@dataclass(frozen=True)
class LoadResult:
    events: pd.DataFrame
    invalid_rows: pd.DataFrame


def load_alert_events(path: str | Path) -> LoadResult:
    """Load and normalize alert interval events from CSV.

    Invalid rows are returned separately instead of silently disappearing.
    Rows with missing ended_at are marked invalid for interval-based analysis.
    """
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out["region"] = out["region"].astype(str).str.strip()
    out["started_at"] = pd.to_datetime(out["started_at"], errors="coerce", utc=True)
    out["ended_at"] = pd.to_datetime(out["ended_at"], errors="coerce", utc=True)
    out["duration_minutes"] = (out["ended_at"] - out["started_at"]).dt.total_seconds() / 60.0

    invalid_mask = (
        out["region"].eq("")
        | out["started_at"].isna()
        | out["ended_at"].isna()
        | out["duration_minutes"].isna()
        | (out["duration_minutes"] <= 0)
    )
    invalid = out[invalid_mask].copy()
    valid = out[~invalid_mask].drop_duplicates().sort_values(["region", "started_at"])
    valid = valid.reset_index(drop=True)
    invalid = invalid.reset_index(drop=True)
    return LoadResult(events=valid, invalid_rows=invalid)
