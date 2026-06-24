# Data

`sample_alerts.csv` is **synthetic** demo data so the project runs immediately after cloning. Its first line is a `#` banner that says so explicitly; the loader skips `#` comment lines, so the banner is ignored by parsing but unmistakable to anyone who opens the file.

It is regenerated deterministically by `scripts/generate_sample_data.py` (`python scripts/generate_sample_data.py`), which injects a deliberately high-contrast `region + hour` pattern:

- **Calm daytime, busy nights:** near-silent hours 07–15, a busy night, and a steep evening ramp (18:00 → 23:00). A Kyiv query reads ~0.01 at midday and ~0.26 → ~0.74 across the evening.
- **Wide regional spread:** busy regions (Kharkiv, Kyiv) read clearly riskier than quiet ones (Lviv, Ivano-Frankivsk).

This makes the risk scores demonstrative and lets the baseline beat a constant base-rate predictor under rolling-origin validation. It is **not** real alert data, and the validation lift reflects the built-in pattern, not forecasting skill.

For real analysis, replace it with a vetted historical air-raid alert dataset with at least:

- `region`
- `started_at`
- `ended_at`

Preferred timestamp format: ISO 8601 with timezone, e.g. `2026-06-01T01:15:00+03:00`.

Do not commit private, sensitive, or restricted datasets without checking licensing and safety constraints.
