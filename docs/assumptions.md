# Assumptions and Limitations

## Input data assumptions

- Each row describes one alert interval for one region.
- Lines beginning with `#` are skipped as comments, so a dataset can carry a provenance banner. The bundled `data/sample_alerts.csv` is synthetic and marked this way on its first line; the loader assumes real alert CSVs do not contain `#` within data fields.
- `started_at` and `ended_at` are parseable datetimes.
- Timezone-aware timestamps are preferred. Naive timestamps are interpreted by pandas and should be avoided in production.
- Raw event timestamps are stored in UTC, but hour-of-day and weekday in all analysis and CLI output are expressed in Europe/Kyiv local time (`DISPLAY_TZ`). Local labels follow the system time-zone database including any daylight-saving transitions, so the spring-forward night skips a local hour and the autumn night repeats one.
- Rows with missing or unparseable `started_at`/`ended_at`, an empty region, or a non-positive duration are flagged as invalid and returned separately in `LoadResult.invalid_rows`. They are not included in the normalized `events` used for the hourly panel or risk baseline.

## Modeling assumptions

- Historical alert frequency can provide useful planning context.
- It is not a reliable prediction of future attacks.
- Chronological validation is required to avoid time-series leakage.
- A constant base-rate baseline is too weak when a daily cycle dominates the signal, so the model is also scored against an hour-of-day climatology; the reported Brier skill score is measured over that stronger bar (positive = skill beyond the daily cycle).
- Region names in real datasets may require normalization.

## Safety limitations

AirAlert Planner is a decision-support prototype. It must not replace official air alert apps, civil defense instructions, or local security guidance.
