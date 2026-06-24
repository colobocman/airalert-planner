from __future__ import annotations

from pathlib import Path

import pandas as pd

from .planner import SAFETY_DISCLAIMER


def _markdown_table(df: pd.DataFrame) -> list[str]:
    """Render a small dataframe as Markdown without optional tabulate dependency."""
    headers = [str(col) for col in df.columns]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for record in df.to_dict(orient="records"):
        rows.append("| " + " | ".join(str(record[col]) for col in df.columns) + " |")
    return rows


def _validation_verdict(validation: dict[str, float]) -> str:
    """One honest line on whether the model beat the base-rate baseline."""
    if validation.get("test_rows", 0.0) <= 0:
        return (
            "Insufficient data for a chronological validation split, so no skill "
            "comparison against the base-rate baseline is available."
        )
    if validation.get("brier", 0.0) < validation.get("baseline_brier", 0.0):
        return (
            "On this run the model beats the base-rate baseline's Brier score, but on a rare "
            "positive class the margin is small — read it as indicative, not proven skill."
        )
    return (
        "On this run the model does not beat the base-rate baseline's Brier score, so the low "
        "absolute MAE/Brier reflect how rare alerts are, not skill."
    )


def write_report(summary: pd.DataFrame, validation: dict[str, float], out_path: str | Path) -> None:
    lines = [
        "# AirAlert Planner Report",
        "",
        "## Summary by region",
        "",
    ]
    if summary.empty:
        lines.append("No valid alert events were found.")
    else:
        lines.extend(_markdown_table(summary))
    lines.extend(
        [
            "",
            "## Chronological validation",
            "",
            f"- MAE: {validation.get('mae', 0.0):.3f} (base-rate baseline {validation.get('baseline_mae', 0.0):.3f})",
            f"- Brier score: {validation.get('brier', 0.0):.3f} (base-rate baseline {validation.get('baseline_brier', 0.0):.3f})",
            f"- Train rows: {validation.get('train_rows', 0.0):.0f}",
            f"- Test rows: {validation.get('test_rows', 0.0):.0f}",
            "",
            _validation_verdict(validation),
            "",
            "Validation uses a single 80/20 chronological split; regions whose alert history ends "
            "before the split boundary may be absent from the test fold, and the hourly panel is "
            "densified over each region's full observed range before splitting. Read the metrics as "
            "indicative, not a rigorous out-of-sample estimate.",
            "",
            "## Safety note",
            "",
            SAFETY_DISCLAIMER,
            "",
        ]
    )
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
