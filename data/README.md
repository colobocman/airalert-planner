# Data

`sample_alerts.csv` is synthetic demo data so the project runs immediately after cloning. It is regenerated deterministically by `scripts/generate_sample_data.py`, which injects a stable `region + hour` pattern (heavier at night and through the evening, some regions far more active than others) so the baseline can demonstrably beat a constant base-rate predictor. It is **not** real alert data.

For real analysis, replace it with a vetted historical air-raid alert dataset with at least:

- `region`
- `started_at`
- `ended_at`

Preferred timestamp format: ISO 8601 with timezone, e.g. `2026-06-01T01:15:00+03:00`.

Do not commit private, sensitive, or restricted datasets without checking licensing and safety constraints.
