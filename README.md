# AirAlert Planner

A small Python product that turns historical Ukrainian air-raid alert intervals into explainable, region-aware risk summaries to help plan trips, events, city visits, and work shifts.

> **Not a real-time safety system.** AirAlert Planner is historical planning support only. It describes how often *comparable past hours* were under an alert — it does **not** predict future attacks, is **not** a real-time alert feed, and must **never** replace official air-alert apps, civil-defense instructions, or local security guidance. The bundled dataset is **synthetic**.

## Contents

- [What it is / who it is for](#what-it-is--who-it-is-for)
- [Repository layout](#repository-layout)
- [What you get](#what-you-get)
- [Quick start (5 minutes)](#quick-start-5-minutes)
- [Example CLI usage](#example-cli-usage)
- [How it works](#how-it-works)
- [Methodology](#methodology)
- [Interpreting the output](#interpreting-the-output)
- [Dataset schema](#dataset-schema)
- [Limitations & safety](#limitations--safety)
- [Next steps / roadmap](#next-steps--roadmap)
- [Development](#development)

## What it is / who it is for

AirAlert Planner loads validated alert intervals from CSV, expands them into an hourly per-region time series, fits an explainable historical-risk baseline with chronological validation, and serves planning-oriented summaries through a CLI (plus an optional thin Telegram wrapper).

It is for anyone deciding **when and where** within Ukraine to schedule something — a trip, an event, a city visit, or a work shift — who wants to read historical alert frequency at a glance, with honest confidence signals and a safety disclaimer attached to every output. The core question it answers: *"Over comparable past hours, how often was this region under an alert?"*

## Repository layout

Core code in `src/airalert_planner/`, tests in `tests/`, design docs in `docs/` (`product_brief.md`, `assumptions.md`), the synthetic dataset and its generator in `data/` and `scripts/`, and generated artifacts in `outputs/` (gitignored). The module-by-module map is in [How it works](#how-it-works).

## What you get

The `risk` command gives a single-region planning summary. Real output (excerpt — the full run also prints the remaining hours, a band legend, and a `risk=` legend line):

```text
Region: Kyiv
Window: 2026-06-26 18:00-22:00 (Europe/Kyiv)
Average historical risk: 0.40 (High)
Relatively lower-risk hour: 18:00 (0.26, Medium)
Relatively higher-risk hour: 21:00 (0.56, High)
- 18:00 risk=0.26 Medium (n=8)
Historical planning support only. Always follow official alerts and local security guidance.
```

Each number is the share of matching past hours that were under an alert (0 = never, 1 = always), with a Low/Medium/High band, a per-hour support count (`n`), and the safety disclaimer always appended.

## Quick start (5 minutes)

**Prerequisites:** Python >= 3.11 (tested on 3.12), `git`, `make`. No API keys, tokens, or external services needed.

1. **Clone the repository and enter it.**
   ```bash
   git clone https://github.com/colobocman/airalert-planner.git
   cd airalert-planner
   ```

2. **Create the virtual environment** (skip if `.venv` already exists).
   ```bash
   python3 -m venv .venv
   ```
   Success: a `.venv/` directory is created (no output).

3. **Activate the venv** (required before every other command — without it the package will not import).
   ```bash
   source .venv/bin/activate
   ```
   Success: your shell prompt is prefixed with `(.venv)`.

4. **Install the package in editable mode with dev extras.**
   ```bash
   pip install -e ".[dev]"
   ```
   Success: ends with `Successfully installed airalert-planner-0.1.0 ...` (plus pandas, numpy, pytest, etc.).

5. **Run the test suite.**
   ```bash
   make test
   ```
   Success: ends with `N passed` and no failures (currently 66, ~10–15s, hardware-dependent; runs `pytest -q`).

6. **Run the analysis pipeline** (writes artifacts to `outputs/`).
   ```bash
   make run
   ```
   Success: prints `Wrote outputs to outputs`, then `Valid events: 1337; invalid rows: 0`, then `Validation: Brier=0.117 vs hour-of-day climatology 0.135 (skill +0.133)`. Creates `outputs/report.md`, `summary.csv`, `regional_risk.csv`, `hourly_panel.csv`, and `figures/`.

7. **Try the planning commands** — a single-region risk summary and a multi-region trip sketch, both shown in full under [Example CLI usage](#example-cli-usage):
   ```bash
   python -m airalert_planner.cli risk --input data/sample_alerts.csv --region Kyiv --date 2026-06-26 --from-hour 18 --to-hour 22
   python -m airalert_planner.cli plan-trip --input data/sample_alerts.csv --regions Lviv Kyiv Kharkiv --date 2026-06-26
   ```
   Each prints a planning summary ending with the safety disclaimer.

> A fresh clone has an empty `outputs/` (its CSVs, report, and figures are gitignored) until you run `make run` — this is expected, not a bug.

## Example CLI usage

**Single-region risk** for an evening window:

```bash
python -m airalert_planner.cli risk --input data/sample_alerts.csv --region Kyiv --date 2026-06-26 --from-hour 18 --to-hour 22
```

Output (excerpt; the full run prints every hour in the window plus the band and `risk=` legend lines):

```text
Region: Kyiv
Window: 2026-06-26 18:00-22:00 (Europe/Kyiv)
Average historical risk: 0.40 (High)
Relatively lower-risk hour: 18:00 (0.26, Medium)
Relatively higher-risk hour: 21:00 (0.56, High)
- 18:00 risk=0.26 Medium (n=8)
Historical planning support only. Always follow official alerts and local security guidance.
```

**Trip sketch** comparing relative risk across a region sequence:

```bash
python -m airalert_planner.cli plan-trip --input data/sample_alerts.csv --regions Lviv Kyiv Kharkiv --date 2026-06-26
```

```text
Route-like regional risk sketch for 2026-06-26
- Lviv: avg daytime risk=0.05 (Low), lower around 13:00
- Kyiv: avg daytime risk=0.15 (Medium), lower around 15:00
- Kharkiv: avg daytime risk=0.22 (Medium), lower around 13:00
This is region-sequence planning, not geospatial routing.
```

> Dates and `--from-hour`/`--to-hour` are Europe/Kyiv local time. On the synthetic sample the matching-hour count per slot is small (e.g. `n=8`).

## How it works

Data flow (the architecture rule, preserved end to end):

```text
data.py -> features.py -> risk.py -> planner.py -> cli.py / telegram_bot.py
```

**Modules**

| Module | Responsibility |
| --- | --- |
| `data.py` | Load & validate alert intervals from CSV (skipping `#` banner lines), parse timestamps to UTC, compute duration, and split valid events from `invalid_rows` (missing region, unparseable times, non-positive duration). |
| `features.py` | Slice intervals into hourly UTC buckets, densify each region's range with explicit zero-alert hours, and attach Europe/Kyiv-local hour, weekday, and `is_night` labels. |
| `risk.py` | Fit a hierarchical shrinkage risk baseline; `predict_one` returns a telescoping estimate; `chronological_validation` runs rolling-origin folds. The headline metric is the **Brier skill score** vs an hour-of-day climatology; `brier_lift` is reported against the weaker base-rate bar (MAE and Brier for the model and both baselines). |
| `planner.py` | Product-facing summaries: `summarize_window` (hourly risk + support + bands + low-confidence flag) and `summarize_trip` (region-sequence sketch). Defines `SAFETY_DISCLAIMER`. |
| `analysis.py` | Descriptive per-region aggregation (alert counts, median/mean duration) feeding the report table. |
| `report.py` | Render `report.md`: per-region table, validation metrics, honest baseline verdicts, and the safety note. |
| `plots.py` | Render three matplotlib PNG figures from the hourly panel. |
| `cli.py` | Thin argparse CLI plus shared `build_model` helper. Subcommands: `analyze`, `risk`, `plan-trip`. |
| `telegram_bot.py` | Optional thin adapter (`/start`, `/help`, `/risk`, `/trip`); reuses `build_model` + `summarize_window` + `summarize_trip`, no duplicated logic; requires `TELEGRAM_BOT_TOKEN` and the `[bot]` extra. |

**`outputs/` artifacts** (created by `make run` / `analyze`)

| Artifact | Contents |
| --- | --- |
| `summary.csv` | Per-region descriptive summary: alert count, median/mean alert duration (minutes). |
| `hourly_panel.csv` | Full densified hourly per-region panel: region, UTC `timestamp_hour`, `alert_active`/`alert_count`/`alert_minutes`, plus local hour/weekday/`is_night`. |
| `regional_risk.csv` | Shrinkage historical risk for every region x weekday (0-6) x hour (0-23). |
| `report.md` | Markdown report: per-region table, chronological-validation metrics with honest verdicts, and safety disclaimer. |
| `figures/alerts_by_hour.png` | Alert-active probability by hour of day (Europe/Kyiv local). |
| `figures/alerts_by_region.png` | Total alert minutes per region, sorted descending. |
| `figures/weekly_trend.png` | Total alert minutes aggregated per ISO week. |

## Methodology

1. **Normalize & validate events.** One row = one alert interval for one region. `#` lines are skipped as comments. Rows with missing/unparseable `started_at`/`ended_at`, empty region, or non-positive duration are flagged invalid and returned separately; only valid events flow downstream. Timestamps are stored in UTC.
2. **Build a densified hourly panel.** Each interval is sliced into hourly buckets (`alert_active`/`alert_count`/`alert_minutes`). Each region's full observed hour range is then filled with explicit zero-alert hours — without this, every observed bucket would be alert-active and risk would trivially be 1.0 everywhere.
3. **Derive local labels.** Bucketing stays in UTC; hour-of-day and weekday labels are computed in Europe/Kyiv (so `--from-hour 18` means 18:00 local), plus an `is_night` flag. Labels follow the system tz database including DST.
4. **Fit a hierarchical shrinkage baseline.** Empirical alert-active rates are computed at global, global+hour, region+hour, and region+weekday+hour levels. `predict_one` telescopes from coarse to fine, blending each level toward its parent by observation count with `PRIOR_STRENGTH = 5.0` pseudo-observations, so a sparse cell needs ~5 real observations before it outweighs broader history. This prevents single-observation cells reporting overconfident 0.0/1.0 risk.
5. **Validate with rolling-origin folds.** `chronological_validation` runs expanding-window cross-validation (sklearn `TimeSeriesSplit`). Splits are on distinct `timestamp_hour` **values**, not row indices, so all same-hour rows stay on one side and no contemporaneous observation leaks across regions via the shared global-hour estimate. Earlier hours train, later hours test; per-fold base rates come from the training slice only.
6. **Score against two baselines.** Per fold the model is scored against (1) an **hour-of-day climatology** that pools all regions/weekdays — the honest bar, since it already captures the dominant daily cycle, so beating it reflects region-level conditioning (on this synthetic, region-structured sample); and (2) a constant **base-rate** predictor (training mean — the weakest bar, easy to beat on a rare positive class). MAE and Brier are reported for the model and both baselines.
7. **Report Brier skill score (headline) and Brier lift.** Fold metrics are averaged equally. The headline `brier_skill_score = 1 - brier / climatology_brier` (0 = no skill beyond the daily cycle, 1 = perfect, negative = worse than climatology; reported as 0.0 if climatology Brier is 0). `brier_lift = baseline_brier - brier` measures improvement over the weakest (base-rate) bar (positive = beats it). The report states honestly how many folds individually beat each baseline.
8. **Translate to Low/Medium/High bands.** The risk fraction is mapped to bands (Low `< 0.10`, Medium `0.10–0.30`, High `>= 0.30`), with lower/higher-risk hour callouts and a low-confidence flag when at most 3 matching past hours exist. Bands are reading heuristics, not safety thresholds; every summary appends the safety disclaimer.

## Interpreting the output

- **Risk number** — the share of matching past hours (region + weekday + hour) that were under an alert, shrunk toward broader history. `0` = never observed under alert, `1` = always. It is **not** a probability of an alert during your specific future window.
- **Risk bands** — `Low` (< 0.10), `Medium` (0.10–0.30), `High` (>= 0.30). Planning heuristics for reading the number at a glance — not safety thresholds and not action triggers.
- **Support (`n`)** — how many matching past hours were observed for that exact slot. `n = 0` means the estimate is borrowed from broader history. Summaries warn when at most 3 matching hours exist (low confidence).
- **Brier skill score** — the headline validation metric: `1 - model_brier / climatology_brier`. `0` means no skill beyond the daily cycle; positive means the model adds region-level conditioning value beyond the daily pattern; negative means worse than climatology. On the synthetic sample the model scores Brier ≈ 0.117 vs climatology ≈ 0.135 (skill ≈ +0.133 vs a **region-pooled** hour-of-day climatology — this isolates region-level conditioning, not weekday effects, since the sample has no weekday signal). It demonstrates the method on a built-in pattern, **not** real forecasting accuracy.
- **Brier lift** — a secondary metric measured over the weakest (base-rate) bar; positive means the model beats a constant predictor. Prefer the Brier skill score as the honest headline.

## Dataset schema

The bundled `data/sample_alerts.csv` is **SYNTHETIC**. Its first line is a `#` provenance banner; the loader skips `#` comment lines.

```text
# SYNTHETIC SAMPLE DATA - generated by scripts/generate_sample_data.py; NOT real air-raid alerts. For demonstration only. See data/README.md.
region,started_at,ended_at
Ivano-Frankivsk,2026-04-06T20:03:00+03:00,2026-04-06T21:43:00+03:00
```

| Column | Meaning |
| --- | --- |
| `region` | Region label (one alert interval = one row for one region). Whitespace is stripped; no alias normalization yet. |
| `started_at` | Alert interval start. Timezone-aware ISO timestamps are preferred; stored internally as UTC. |
| `ended_at` | Alert interval end. Must be after `started_at` (non-positive durations are flagged invalid). |

The sample file has 1339 lines = 1 banner + 1 header + 1337 valid events (matching `Valid events: 1337`). Its lift reflects a deliberately high-contrast built-in region+hour pattern, not real forecasting accuracy.

## Limitations & safety

- **Synthetic data.** The bundled sample is generated deterministically with a high-contrast region+hour pattern. All reported lift demonstrates the *method*, not real-world predictive performance.
- **Not real-time, not predictive.** Historical frequency does not forecast future attacks with operational certainty. This is decision-support only.
- **Skill reflects region-level, not weekday, conditioning.** The honest baseline pools all regions/weekdays into an hour-of-day climatology, so beating it isolates region-level value, not weekday effects.
- **No weekday signal in the sample by construction.** The generator's alert probability depends only on region and hour; the region+weekday+hour cell is plumbed but unexercised on this data.
- **Route support is region-sequence, not geospatial.** `plan-trip` reports each region's daytime risk independently — no path, distance, or transit-timing matching.
- **No region-name normalization.** The loader only strips whitespace; multi-source feeds would fragment a region across spelling/transliteration variants (e.g. Kyiv vs Kiev).
- **Point estimate, no interval.** Risk is a single shrinkage value plus a coarse support count and a low-confidence flag — no confidence/credible interval is shown.
- **Bands are heuristics, not calibrated thresholds.** The 0.10 / 0.30 cutoffs are fixed planning aids over the historical fraction.
- **Densification spans observed windows only.** Each region's calendar is filled only between its first and last alert hour; uncovered periods contribute no zero-hours, so the global mean is not a true full-calendar base rate.
- **DST edge cases.** Local labels follow Europe/Kyiv including DST, so the spring-forward night skips a local hour and the autumn night repeats one, affecting hour-bucket counts around transitions.
- **Telegram bot is the least-developed surface.** It exposes `/start`, `/help`, `/risk`, and `/trip` (delegating to the same planner functions as the CLI, with tests for the parse/error paths), but it is intentionally optional and unmonitored — not a real-time channel.

**Safety disclaimer (attached to every output, verbatim):**

> Historical planning support only. Always follow official alerts and local security guidance.

## Next steps / roadmap

| Next step | Why | Effort |
| --- | --- | --- |
| Swap to a per-region-hour climatology baseline to isolate weekday value | The current baseline pools all regions, so the skill score measures region-level (not weekday) conditioning. A region+hour bar would attribute lift to the weekday dimension the model already fits. Pure addition in `risk.py` + tests; no API change. | small, ~0.5 day |
| Add a weekday/seasonality signal to the sample generator | The generator's probability ignores day-of-week, so the weekday cell has nothing to learn and the baseline above would show zero weekday lift by construction. A small, documented, deterministic weekday/seasonal term makes the plumbing testable. Touches `scripts/generate_sample_data.py`. | small, ~0.5–1 day |
| Report confidence intervals on the risk number | `summarize_window` emits only a point estimate plus support and a low-confidence flag. A Wilson/Jeffreys (or beta-posterior) interval per hour lets planners judge uncertainty. Self-contained `risk.py` + `planner.py` change with tests. | medium, ~1–2 days |
| Integrate a vetted real historical source + live official-alert lookup | All current data is synthetic. A loader feeding the same `data.py -> features.py` pipeline moves this from demo to product; a live official-alert pointer keeps the not-real-time, not-predictive stance intact. Adds external dependency, schema mapping, provenance. | large, multi-day |
| Add region-name normalization in the data layer | The loader only strips whitespace, so multi-source feeds split one region across variants (Kyiv/Kiev, oblast suffixes). A canonical alias map applied at load time hardens per-region cells. Localized to `data.py` + a mapping file + tests. | small-medium, ~1 day |
| Implement geospatial route matching for `plan-trip` | Today a route is an effectively unordered list of region risks with no geography or timing. Real routing maps a path to regions crossed at expected times. Gated by `CLAUDE.md` until the MVP core is complete; pulls in a geo dependency. | large, multi-day |

## Development

```bash
make test                                    # pytest -q  (currently 66 tests, ~10–15s)
make run                                      # full pipeline -> outputs/
ruff check src tests                          # lint (make lint)
python scripts/generate_sample_data.py        # regenerate the synthetic data/sample_alerts.csv
make clean                                    # remove generated outputs/ and caches
```

- **Architecture rule:** preserve `data.py -> features.py -> risk.py -> planner.py -> cli.py / telegram_bot.py`. Keep business logic in core modules; keep the CLI and bot thin.
- **Modeling rules:** explainable baselines, chronological validation only (no random splits for time-series behavior), no real-time predictive-safety claims, and always carry the safety disclaimer.
- **Claude Code workflow:** see `CLAUDE.md` for the project guide (mission, scope guardrails, modeling rules, review checklist) and `docs/assumptions.md` for documented assumptions and limitations.
- **Optional Telegram wrapper:** install with `pip install -e ".[bot]"`, set `TELEGRAM_BOT_TOKEN`, then run `python -m airalert_planner.telegram_bot --input data/sample_alerts.csv`. The rest of the project has no dependency on it.
