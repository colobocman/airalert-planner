# Product Brief: AirAlert Planner

## One-line summary

AirAlert Planner turns historical Ukrainian air raid alert time series into explainable planning guidance for trips, city visits, events, and work shifts.

## Target users

- Travelers planning intercity movement.
- Event organizers choosing safer time windows.
- Operations managers planning on-site shifts.
- Analysts who need a reproducible baseline before investing in heavier forecasting models.

## MVP promise

Given historical alert events, the MVP answers:

- Which regions have higher historical alert intensity?
- Which hours and weekdays look relatively higher or lower risk?
- What is the historical risk profile for a selected city/time window?
- How could a route-like sequence of regions be compared at a high level?

## Non-goals

- No real-time safety advice.
- No tactical forecasting claims.
- No neural-network complexity in the first MVP.
- No full route geospatial matching before the core analysis is validated.

## Product architecture

The core must remain independent from interfaces:

```text
alert events -> hourly time-series panel -> explainable risk baseline -> planner service -> CLI / Telegram adapter
```

## Success criteria

- A reviewer can run the project locally without external credentials.
- The analytical core has tests.
- The CLI produces practical planning output.
- Limitations are explicit and conservative.
- The Telegram wrapper is optional and does not duplicate business logic.
