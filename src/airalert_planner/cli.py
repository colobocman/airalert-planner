from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import summarize_events
from .data import load_alert_events
from .features import build_hourly_panel
from .planner import summarize_trip, summarize_window
from .plots import save_plots
from .report import write_report
from .risk import chronological_validation, fit_risk_model, risk_table


def build_model(input_path: str):
    loaded = load_alert_events(input_path)
    panel = build_hourly_panel(loaded.events)
    model = fit_risk_model(panel)
    return loaded, panel, model


def cmd_analyze(args: argparse.Namespace) -> None:
    out = Path(args.out)
    figures = out / "figures"
    out.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    loaded, panel, model = build_model(args.input)
    summary = summarize_events(loaded.events)
    validation = chronological_validation(panel)
    regions = sorted(loaded.events["region"].unique().tolist()) if not loaded.events.empty else []
    risks = risk_table(model, regions)

    summary.to_csv(out / "summary.csv", index=False)
    panel.to_csv(out / "hourly_panel.csv", index=False)
    risks.to_csv(out / "regional_risk.csv", index=False)
    save_plots(panel, figures)
    write_report(summary, validation, out / "report.md")

    print(f"Wrote outputs to {out}")
    print(f"Valid events: {len(loaded.events)}; invalid rows: {len(loaded.invalid_rows)}")
    print(
        f"Validation: Brier={validation['brier']:.3f} "
        f"vs hour-of-day climatology {validation['climatology_brier']:.3f} "
        f"(skill {validation['brier_skill_score']:+.3f})"
    )


def cmd_risk(args: argparse.Namespace) -> None:
    _, _, model = build_model(args.input)
    summary = summarize_window(model, args.region, args.date, args.from_hour, args.to_hour)
    print(summary.to_text())


def cmd_plan_trip(args: argparse.Namespace) -> None:
    _, _, model = build_model(args.input)
    print(summarize_trip(model, args.regions, args.date))


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AirAlert Planner CLI")
    sub = parser.add_subparsers(required=True)

    analyze = sub.add_parser("analyze", help="Run full analysis pipeline")
    analyze.add_argument("--input", required=True)
    analyze.add_argument("--out", default="outputs")
    analyze.set_defaults(func=cmd_analyze)

    risk = sub.add_parser("risk", help="Summarize historical risk for a region/time window")
    risk.add_argument("--input", default="data/sample_alerts.csv")
    risk.add_argument("--region", required=True)
    risk.add_argument("--date", required=True)
    risk.add_argument("--from-hour", type=int, required=True, help="start hour 0-23, Europe/Kyiv local time")
    risk.add_argument("--to-hour", type=int, required=True, help="end hour 1-24 (exclusive), Europe/Kyiv local time")
    risk.set_defaults(func=cmd_risk)

    trip = sub.add_parser("plan-trip", help="Summarize a route-like sequence of regions")
    trip.add_argument("--input", default="data/sample_alerts.csv")
    trip.add_argument("--regions", nargs="+", required=True)
    trip.add_argument("--date", required=True)
    trip.set_defaults(func=cmd_plan_trip)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
