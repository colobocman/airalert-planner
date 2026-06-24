# AirAlert Planner

A lightweight Python decision-support MVP that analyzes historical Ukrainian air raid alert time series and turns them into practical planning guidance for trips, city visits, events, and work shifts.

The project intentionally keeps a clear boundary: it uses historical patterns for planning support. It is **not** a real-time safety system and must never replace official alerts or local security guidance.

## Product idea

People often need to decide *when* to travel, host a meeting, run an onsite shift, or visit a city. AirAlert Planner helps answer a narrow, explainable question:

> Based on historical alert patterns, which regions and time windows have relatively higher or lower alert intensity?

The first MVP exposes this through a reproducible CLI. A Telegram bot wrapper is included as an optional thin adapter over the same planner service.

## What it does

- Loads historical alert events with `region`, `started_at`, and `ended_at`.
- Normalizes timestamps and durations.
- Converts alert intervals into an hourly regional time-series panel.
- Builds an explainable historical-frequency risk baseline.
- Runs rolling-origin (expanding-window) chronological validation — not a random split — reported as Brier *lift* over a constant base-rate baseline so a low score on rare alerts is not mistaken for skill.
- Generates summary CSV files, charts, and a Markdown report.
- Provides a CLI planning assistant for region/time-window risk queries, labelling each hour Low/Medium/High for trip, event, and shift timing.
- Provides optional Telegram bot wiring without duplicating core logic.

## Quick start

```bash
git clone https://github.com/colobocman/airalert-planner.git
cd airalert-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make test
make run
```

Generated artifacts appear in `outputs/`.

## Example CLI usage

Run the full pipeline on the sample dataset:

```bash
make run
```

Query a specific planning window:

```bash
python -m airalert_planner.cli risk \
  --input data/sample_alerts.csv \
  --region Kyiv \
  --date 2026-06-26 \
  --from-hour 18 \
  --to-hour 22
```

Hours are Europe/Kyiv local time, so `--from-hour 18` means 18:00 in Kyiv.

The window average and every hour are labelled with an interpretation band — **Low** (below 0.10), **Medium** (0.10–0.30), or **High** (0.30 or higher) — and the output explains each band inline, so a trip, event, or shift can be timed against the historically quieter hours. The bands are planning heuristics over historical frequency, not safety predictions; the safety disclaimer is always printed.

Compare a sequence of regions for a route-like plan:

```bash
python -m airalert_planner.cli plan-trip \
  --input data/sample_alerts.csv \
  --regions Ivano-Frankivsk Lviv Rivne Zhytomyr Kyiv \
  --date 2026-06-26
```

Optional Telegram bot:

```bash
export TELEGRAM_BOT_TOKEN="<token>"
python -m airalert_planner.telegram_bot --input data/sample_alerts.csv
```

Bot commands:

```text
/help
/risk Kyiv 2026-06-26 18 22
```

## Dataset schema

The MVP expects CSV rows like:

```csv
region,started_at,ended_at
Kyiv,2026-06-01T01:15:00+03:00,2026-06-01T02:40:00+03:00
```

Required fields:

- `region`: region or city label.
- `started_at`: alert start time, ISO-like datetime.
- `ended_at`: alert end time, ISO-like datetime. Rows with a missing/unparseable `ended_at` or a non-positive duration are reported as invalid rows and excluded from analysis.

See `data/README.md` and `docs/assumptions.md`.

## Methodology

1. **Normalize events** — parse timestamps, compute duration, flag invalid rows.
2. **Build hourly panel** — split interval events into hourly buckets by region.
3. **Create features** — hour, weekday, night/day, alert minutes. Hour and weekday are expressed in Europe/Kyiv local time, so a query for hour 18 means 18:00 in Kyiv.
4. **Fit baseline** — for each `region + weekday + hour`, risk is the share of those past hours that were under an alert (0 = never, 1 = always), smoothed toward broader averages when history is thin.
5. **Fallback for sparse data** — use `region + hour`, then `global hour`, then global mean.
6. **Validate chronologically** — rolling-origin (expanding-window) folds: each fold trains on earlier hours and is scored on later ones, never the reverse, always alongside a constant base-rate baseline. The headline number is Brier *lift* over that baseline. Because alerts are a rare positive class, low absolute MAE/Brier are easy to obtain, so only positive lift counts as skill. On the bundled synthetic sample — which carries a deliberate, time-stable region+hour pattern — the model beats the baseline; this demonstrates the method, not real-world predictive certainty.
7. **Expose planning interface** — turn risk scores into practical guidance for selected windows.

## Why a simple baseline?

The goal of this MVP is a dependable, explainable product core. A neural model would be premature without enough data volume, careful validation, and operational evaluation. A transparent historical baseline is easier to inspect, debug, and improve.

## Limitations

- Historical risk patterns do not predict future attacks with operational certainty.
- The sample dataset is synthetic, generated by `scripts/generate_sample_data.py` with a deliberate pattern to demonstrate the method; it is not real alert data, so the validation lift reflects that built-in pattern, not forecasting accuracy.
- Real deployment needs a vetted historical alert source and live official alert integration.
- Region names require normalization before large-scale production use.
- Route-level support currently approximates risk by region sequence, not geospatial path matching.

## Development workflow with Claude Code

This repository includes `CLAUDE.md`, `.claude/agents/`, `.claude/skills/`, and `.claude/commands/` to keep Claude focused on product-quality, time-series correctness, and MVP discipline.

Start Claude Code from the repo root:

```bash
claude
```

Recommended first prompt:

```text
Read CLAUDE.md and docs/product_brief.md. Then propose the next smallest implementation step. Do not overbuild; preserve the analytical core and CLI product interface.
```

## Safety note

This project is planning support based on historical data. Always use official air-alert channels and local security instructions for real-world decisions.
