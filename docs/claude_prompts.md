# Claude Prompt Playbook

These prompts intentionally describe the product and engineering constraints without referencing any external selection process.

## 1. Product framing

```text
We are building AirAlert Planner: a Python MVP that analyzes historical Ukrainian air raid alert time series and helps users plan trips, events, city visits, and work shifts using explainable regional/hourly risk patterns.

Before writing code, act as a skeptical product + ML architect. Define target users, MVP user stories, non-goals, analytical architecture, validation strategy, and risks of overbuilding. Keep the scope realistic and product-oriented.
```

## 2. Architecture

```text
Read CLAUDE.md and docs/product_brief.md. Design the next smallest implementation step. Preserve this architecture: data normalization -> hourly time-series panel -> risk baseline -> planner service -> CLI/optional Telegram adapter. Do not overbuild.
```

## 3. Data layer

```text
Implement only the data loading and normalization layer. Parse region, started_at, ended_at; compute duration_minutes; handle missing or invalid timestamps explicitly; add pytest tests. Do not implement risk model or bot yet.
```

## 4. Feature layer

```text
Implement hourly feature generation. Split alert intervals into hourly buckets with alert_active, alert_count, alert_minutes, hour, weekday, and is_night. Tests must cover midnight-spanning alerts.
```

## 5. Risk model

```text
Implement an explainable historical-frequency baseline. Use chronological validation only, no random split. Add sparse-data fallbacks and tests. Document limitations and avoid real-time prediction claims.
```

## 6. Planning assistant

```text
Build a CLI planning assistant on top of the risk model. It should summarize risk for a region/date/time window, identify relatively better/worse hours, and include a safety disclaimer.
```

## 7. Harsh review

```text
Act as a harsh product-minded data engineering reviewer. Check task focus, reproducibility, time-series leakage, overclaiming, missing tests, product usefulness, and README clarity. Prioritize fixes that matter now. Do not suggest large new features.
```
