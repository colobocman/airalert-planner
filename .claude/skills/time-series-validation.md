# Time-Series Validation Rules

Use this skill whenever changing risk or forecasting logic.

Rules:
- Never use random train/test split for time-dependent evaluation.
- Split chronologically by timestamp.
- Fit baselines only on training history.
- Evaluate on later timestamps.
- Document sparse data and uncertainty.
- Prefer explainable baseline before complex ML.
