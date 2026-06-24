# Claude Code Project Guide: AirAlert Planner

## Mission

Build a practical Python MVP that analyzes historical Ukrainian air raid alert time series and exposes the results through a small planning assistant for trips, events, city visits, and work shifts.

Do **not** frame this as an academic exercise. Build a small, working product core.

## Architecture rule

Always preserve this separation:

```text
data.py -> features.py -> risk.py -> planner.py -> cli.py / telegram_bot.py
```

- `data.py`: load and validate alert events.
- `features.py`: convert intervals into hourly regional time-series panel.
- `risk.py`: explainable historical risk baseline and chronological validation.
- `planner.py`: product-facing planning summaries.
- `cli.py`: reproducible local interface.
- `telegram_bot.py`: optional thin adapter only; no duplicated business logic.

## Scope guardrails

Prioritize in this order:

1. Working analytical core.
2. Tests for data/features/risk/planner.
3. CLI product interface.
4. README/report quality.
5. Optional Telegram wrapper.

Do not implement a web app, complex neural model, real-time alert ingestion, or geospatial route engine unless the MVP is already complete.

## Modeling rules

- Start with explainable baselines.
- Use chronological validation only.
- Do not use random train/test split for time-series behavior.
- Do not claim real-time predictive safety.
- Always include limitations and safety disclaimer.

## Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
make run
python -m airalert_planner.cli risk --input data/sample_alerts.csv --region Kyiv --date 2026-06-26 --from-hour 18 --to-hour 22
```

## Coding standards

- Keep code simple and readable.
- Add tests before or alongside behavior changes.
- Prefer pure functions in core modules.
- Keep CLI thin.
- No secrets in the repository.
- If a suggestion increases scope, first explain the tradeoff and propose the smaller alternative.

## Review checklist

Before calling work complete:

- `pytest` passes.
- `make run` generates outputs.
- CLI risk command returns a useful planning summary.
- README explains quick start, methodology, limitations, and product use.
- No hidden dependency on Telegram token or external services.
