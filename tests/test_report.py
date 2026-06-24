from pathlib import Path

import pandas as pd

from airalert_planner.report import write_report

SUMMARY = pd.DataFrame(
    [{"region": "Kyiv", "alerts": 3, "median_duration_minutes": 60.0, "mean_duration_minutes": 70.0}]
)


def _write(tmp_path: Path, validation: dict) -> str:
    out = tmp_path / "report.md"
    write_report(SUMMARY, validation, out)
    return out.read_text()


def test_report_states_model_does_not_beat_baseline(tmp_path: Path):
    text = _write(
        tmp_path,
        {"mae": 0.092, "brier": 0.066, "baseline_mae": 0.096, "baseline_brier": 0.063, "train_rows": 660.0, "test_rows": 165.0},
    )

    # Baseline surfaced, and the verdict is computed from the numbers.
    assert "base-rate" in text.lower()
    assert "0.063" in text
    assert "does not beat" in text.lower()


def test_report_states_model_beats_baseline(tmp_path: Path):
    text = _write(
        tmp_path,
        {"mae": 0.04, "brier": 0.050, "baseline_mae": 0.06, "baseline_brier": 0.063, "train_rows": 660.0, "test_rows": 165.0},
    )

    assert "beats the base-rate" in text.lower()
    assert "does not beat" not in text.lower()


def test_report_surfaces_rolling_origin_folds_and_lift(tmp_path: Path):
    text = _write(
        tmp_path,
        {
            "mae": 0.04, "brier": 0.050, "baseline_mae": 0.06, "baseline_brier": 0.063,
            "brier_lift": 0.013, "n_splits": 4, "train_rows": 660.0, "test_rows": 165.0,
        },
    )

    # The report must disclose the validation method (rolling-origin folds) and
    # the headline lift over the base rate, not imply a single fragile split.
    assert "4 rolling-origin" in text.lower()
    assert "lift" in text.lower()


def test_report_verdict_notes_fold_agreement(tmp_path: Path):
    text = _write(
        tmp_path,
        {
            "mae": 0.04, "brier": 0.050, "baseline_mae": 0.06, "baseline_brier": 0.063,
            "brier_lift": 0.013, "n_splits": 4, "train_rows": 660.0, "test_rows": 165.0,
            "folds": [
                {"brier": 0.04, "baseline_brier": 0.06},
                {"brier": 0.05, "baseline_brier": 0.06},
                {"brier": 0.07, "baseline_brier": 0.06},
                {"brier": 0.055, "baseline_brier": 0.063},
            ],
        },
    )

    # Averaged lift can hide fold disagreement; the verdict must say how many
    # folds individually beat the baseline (here 3 of 4).
    assert "3 of 4 folds" in text.lower()


def test_report_flags_insufficient_validation_data(tmp_path: Path):
    text = _write(
        tmp_path,
        {"mae": 0.0, "brier": 0.0, "baseline_mae": 0.0, "baseline_brier": 0.0, "train_rows": 2.0, "test_rows": 0.0},
    )

    # With no test rows there is no skill comparison; don't render a verdict.
    assert "insufficient" in text.lower()
    assert "does not beat" not in text.lower()
    assert "beats the base-rate" not in text.lower()
