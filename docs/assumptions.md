# Assumptions and Limitations

## Input data assumptions

- Each row describes one alert interval for one region.
- `started_at` and `ended_at` are parseable datetimes.
- Timezone-aware timestamps are preferred. Naive timestamps are interpreted by pandas and should be avoided in production.
- Rows with missing `ended_at` are preserved in normalized data but excluded from hourly-panel calculations unless a later policy is added.

## Modeling assumptions

- Historical alert frequency can provide useful planning context.
- It is not a reliable prediction of future attacks.
- Chronological validation is required to avoid time-series leakage.
- Region names in real datasets may require normalization.

## Safety limitations

AirAlert Planner is a decision-support prototype. It must not replace official air alert apps, civil defense instructions, or local security guidance.
