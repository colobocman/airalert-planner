from pathlib import Path

import pandas as pd

from airalert_planner.cli import main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = str(ROOT / "data" / "sample_alerts.csv")


def test_analyze_writes_outputs_with_variation(tmp_path: Path):
    out = tmp_path / "outputs"

    main(["analyze", "--input", SAMPLE, "--out", str(out)])

    for name in ["summary.csv", "hourly_panel.csv", "regional_risk.csv", "report.md"]:
        assert (out / name).exists()

    # The shipped bug produced all-zero risk everywhere; guard the regression.
    risks = pd.read_csv(out / "regional_risk.csv")
    assert risks["risk"].nunique() > 1
    assert risks["risk"].max() > 0.0


def test_risk_command_prints_non_degenerate_window(capsys):
    main(
        [
            "risk",
            "--input",
            SAMPLE,
            "--region",
            "Kyiv",
            "--date",
            "2026-06-26",
            "--from-hour",
            "18",
            "--to-hour",
            "22",
        ]
    )
    out = capsys.readouterr().out

    assert "Kyiv" in out
    # Parse the numeric per-hour risks and assert the window is genuinely
    # differentiated and non-zero, not merely producing distinct strings.
    risks = [float(line.split("risk=")[1].split()[0]) for line in out.splitlines() if "risk=" in line]
    assert len(risks) >= 2
    assert max(risks) > min(risks)
    assert max(risks) > 0.0
