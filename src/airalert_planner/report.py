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


def _fold_agreement(validation: dict[str, object]) -> str:
    """' (M of N folds individually beat it)' when per-fold detail is available."""
    folds = validation.get("folds") or []
    if not folds:
        return ""
    beat = sum(1 for fold in folds if fold["brier"] < fold["baseline_brier"])
    return f" ({beat} of {len(folds)} folds individually beat it)"


def _validation_verdict(validation: dict[str, object]) -> str:
    """One honest line on whether the model beat the base-rate baseline."""
    if validation.get("test_rows", 0.0) <= 0:
        return (
            "Insufficient data for a chronological validation split, so no skill "
            "comparison against the base-rate baseline is available."
        )
    if validation.get("brier", 0.0) < validation.get("baseline_brier", 0.0):
        return (
            "On this run the model beats the base-rate baseline's Brier score"
            f"{_fold_agreement(validation)}, but on a rare positive class the margin is small "
            "— read it as indicative, not proven skill."
        )
    return (
        "On this run the model does not beat the base-rate baseline's Brier score"
        f"{_fold_agreement(validation)}, so the low absolute MAE/Brier reflect how rare alerts "
        "are, not skill."
    )


def _climatology_verdict(validation: dict[str, object]) -> str:
    """Honest line on the stronger bar: the hour-of-day climatology.

    Beating a constant base rate is near-trivial when a daily cycle dominates;
    the climatology strips that cycle out, so this is the test that matters.
    """
    if validation.get("test_rows", 0.0) <= 0 or "climatology_brier" not in validation:
        return ""
    if validation.get("brier", 0.0) < validation.get("climatology_brier", 0.0):
        return (
            "It also beats an hour-of-day climatology baseline (pooled across regions), so the "
            "model's region-level conditioning adds value beyond the average daily cycle. (This "
            "bar pools regions, so it does not isolate weekday effects.)"
        )
    return (
        "It does not beat an hour-of-day climatology baseline, so on this data the daily cycle "
        "explains the result and the model's extra conditioning adds little."
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
    n_splits = int(validation.get("n_splits", 0))
    validation_lines = [
        "",
        "## Chronological validation",
        "",
        f"- MAE: {validation.get('mae', 0.0):.3f} (base-rate baseline {validation.get('baseline_mae', 0.0):.3f})",
        f"- Brier score: {validation.get('brier', 0.0):.3f} (base-rate baseline {validation.get('baseline_brier', 0.0):.3f})",
    ]
    if "climatology_brier" in validation:
        validation_lines.append(
            f"- Hour-of-day climatology Brier: {validation.get('climatology_brier', 0.0):.3f} "
            "(stronger bar: strips out the daily cycle)"
        )
    if n_splits > 0:
        validation_lines.append(
            f"- Brier lift over base rate: {validation.get('brier_lift', 0.0):+.3f} (positive = model adds skill)"
        )
        if "climatology_brier" in validation:
            validation_lines.append(
                f"- Brier skill score vs climatology: {validation.get('brier_skill_score', 0.0):+.3f} "
                "(0 = no skill beyond the daily cycle, 1 = perfect)"
            )
        validation_lines.append(f"- Method: {n_splits} rolling-origin (expanding-window) folds")
    validation_lines.extend(
        [
            f"- Train rows (largest fold): {validation.get('train_rows', 0.0):.0f}",
            f"- Test rows (across folds): {validation.get('test_rows', 0.0):.0f}",
            "",
            _validation_verdict(validation),
        ]
    )
    climatology_verdict = _climatology_verdict(validation)
    if climatology_verdict:
        validation_lines.append(climatology_verdict)
    validation_lines.append("")
    if n_splits > 0:
        validation_lines.append(
            "Validation uses rolling-origin (expanding-window) chronological folds split on whole "
            "timestamps, so every test hour is scored by a model trained only on earlier hours. The "
            "hourly panel is densified over each region's full observed range before folding, and "
            "short-history regions contribute fewer test rows. Read the metrics as indicative, not "
            "a production-grade out-of-sample guarantee."
        )
        validation_lines.append("")
    validation_lines.extend(["## Safety note", "", SAFETY_DISCLAIMER, ""])
    lines.extend(validation_lines)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
