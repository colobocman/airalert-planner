from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def save_plots(panel: pd.DataFrame, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if panel.empty:
        return

    by_hour = panel.groupby("hour")["alert_active"].mean()
    fig, ax = plt.subplots(figsize=(8, 4))
    by_hour.plot(kind="bar", ax=ax, title="Historical alert activity by hour")
    ax.set_ylabel("Alert-active probability")
    fig.tight_layout()
    fig.savefig(out / "alerts_by_hour.png")
    plt.close(fig)

    by_region = panel.groupby("region")["alert_minutes"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    by_region.plot(kind="bar", ax=ax, title="Alert minutes by region")
    ax.set_ylabel("Alert minutes")
    fig.tight_layout()
    fig.savefig(out / "alerts_by_region.png")
    plt.close(fig)

    trend_source = panel.assign(timestamp_naive=panel["timestamp_hour"].dt.tz_convert(None))
    trend = trend_source.assign(week=trend_source["timestamp_naive"].dt.to_period("W").astype(str)).groupby("week")["alert_minutes"].sum()
    fig, ax = plt.subplots(figsize=(8, 4))
    trend.plot(kind="line", marker="o", ax=ax, title="Weekly alert-minute trend")
    ax.set_ylabel("Alert minutes")
    fig.tight_layout()
    fig.savefig(out / "weekly_trend.png")
    plt.close(fig)
