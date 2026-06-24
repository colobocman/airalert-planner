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
            f"- MAE: {validation.get('mae', 0.0):.3f}",
            f"- Brier score: {validation.get('brier', 0.0):.3f}",
            f"- Train rows: {validation.get('train_rows', 0.0):.0f}",
            f"- Test rows: {validation.get('test_rows', 0.0):.0f}",
            "",
            "## Safety note",
            "",
            SAFETY_DISCLAIMER,
            "",
        ]
    )
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
