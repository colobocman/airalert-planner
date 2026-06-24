from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import brier_score_loss, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

# Pseudo-observations pulling a thinly-supported cell toward its parent
# estimate. A cell needs roughly this many real observations before it
# outweighs its parent, which stops single-observation cells from reporting
# overconfident 0.0 / 1.0 risk.
PRIOR_STRENGTH = 5.0


def _shrink(cell_mean: float, cell_n: float, parent: float, strength: float) -> float:
    """Blend a cell's empirical mean toward its parent estimate by support."""
    return (cell_n * cell_mean + strength * parent) / (cell_n + strength)


@dataclass(frozen=True)
class RiskModel:
    by_region_weekday_hour: pd.DataFrame
    by_region_hour: pd.DataFrame
    by_global_hour: pd.DataFrame
    global_mean: float
    prior_strength: float = PRIOR_STRENGTH

    def predict_one(self, region: str, weekday: int, hour: int) -> float:
        """Shrinkage estimate: global -> global+hour -> region+hour -> region+weekday+hour.

        Each more specific level is blended toward the running estimate built
        from the coarser levels beneath it (a telescoping shrinkage), weighted by
        how many observations support it. Sparse cells defer to that estimate
        instead of overfitting a handful of hours.
        """
        strength = self.prior_strength
        estimate = self.global_mean

        gh = self.by_global_hour
        mask = gh["hour"] == hour
        if mask.any():
            row = gh.loc[mask].iloc[0]
            estimate = _shrink(float(row["risk"]), float(row["n"]), estimate, strength)

        rh = self.by_region_hour
        mask = (rh["region"] == region) & (rh["hour"] == hour)
        if mask.any():
            row = rh.loc[mask].iloc[0]
            estimate = _shrink(float(row["risk"]), float(row["n"]), estimate, strength)

        rwh = self.by_region_weekday_hour
        mask = (rwh["region"] == region) & (rwh["weekday"] == weekday) & (rwh["hour"] == hour)
        if mask.any():
            row = rwh.loc[mask].iloc[0]
            estimate = _shrink(float(row["risk"]), float(row["n"]), estimate, strength)

        return float(estimate)

    def support_one(self, region: str, weekday: int, hour: int) -> int:
        """Observations of this exact region+weekday+hour slot, else 0.

        Deliberately does NOT fall back to coarser levels: a value of 0 means
        this specific slot was never observed and the estimate is borrowed from
        broader history -- exactly when the low-confidence flag should fire.
        Reporting the region+hour count here would overstate the evidence for an
        unseen weekday and silently suppress that warning.
        """
        rwh = self.by_region_weekday_hour
        mask = (rwh["region"] == region) & (rwh["weekday"] == weekday) & (rwh["hour"] == hour)
        if mask.any():
            return int(rwh.loc[mask, "n"].iloc[0])
        return 0


def _grouped_rate(panel: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Mean alert-active rate and observation count for a grouping."""
    return panel.groupby(keys, as_index=False).agg(
        risk=("alert_active", "mean"), n=("alert_active", "size")
    )


def fit_risk_model(panel: pd.DataFrame) -> RiskModel:
    if panel.empty:
        return RiskModel(
            pd.DataFrame(columns=["region", "weekday", "hour", "risk", "n"]),
            pd.DataFrame(columns=["region", "hour", "risk", "n"]),
            pd.DataFrame(columns=["hour", "risk", "n"]),
            0.0,
        )

    by_region_weekday_hour = _grouped_rate(panel, ["region", "weekday", "hour"])
    by_region_hour = _grouped_rate(panel, ["region", "hour"])
    by_global_hour = _grouped_rate(panel, ["hour"])
    global_mean = float(panel["alert_active"].mean())
    return RiskModel(by_region_weekday_hour, by_region_hour, by_global_hour, global_mean)


def risk_table(model: RiskModel, regions: list[str]) -> pd.DataFrame:
    rows = []
    for region in regions:
        for weekday in range(7):
            for hour in range(24):
                risk = round(model.predict_one(region, weekday, hour), 4)
                rows.append({"region": region, "weekday": weekday, "hour": hour, "risk": risk})
    return pd.DataFrame(rows)


def _score_fold(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    """Fit on the train slice and score the model and base-rate baseline on test."""
    model = fit_risk_model(train)
    preds = [model.predict_one(row.region, int(row.weekday), int(row.hour)) for row in test.itertuples(index=False)]
    y = test["alert_active"].astype(float).to_list()

    # Constant base-rate predictor: the bar the model must clear. On a rare
    # positive class, low absolute MAE/Brier mean little unless they beat this.
    base_rate = float(train["alert_active"].mean())
    baseline = [base_rate] * len(y)
    return {
        "mae": float(mean_absolute_error(y, preds)),
        "brier": float(brier_score_loss(y, preds)),
        "baseline_mae": float(mean_absolute_error(y, baseline)),
        "baseline_brier": float(brier_score_loss(y, baseline)),
        "train_rows": float(len(train)),
        "test_rows": float(len(test)),
    }


def _rolling_folds(ordered: pd.DataFrame, n_splits: int):
    """Yield (train, test) frames split on whole timestamps (rolling origin).

    Splitting on distinct ``timestamp_hour`` values -- not row indices -- keeps
    every row sharing a timestamp on the same side of the cut. Otherwise a
    boundary that falls inside a group of same-hour rows from different regions
    would let one region's contemporaneous observation leak into another
    region's prediction through the shared global-hour estimate.
    """
    unique_ts = ordered["timestamp_hour"].drop_duplicates().sort_values().reset_index(drop=True)
    for train_idx, test_idx in TimeSeriesSplit(n_splits=n_splits).split(unique_ts):
        train_ts = set(unique_ts.iloc[train_idx])
        test_ts = set(unique_ts.iloc[test_idx])
        yield (
            ordered[ordered["timestamp_hour"].isin(train_ts)],
            ordered[ordered["timestamp_hour"].isin(test_ts)],
        )


def chronological_validation(panel: pd.DataFrame, n_splits: int = 4) -> dict[str, object]:
    """Rolling-origin validation: expanding-window folds, earlier hours train, later hours test.

    A single 80/20 cut makes the metric hostage to one split point. Several
    expanding-window folds (rolling origin) average that out and never let a
    test row inform its own training data.
    """
    insufficient = {
        "mae": 0.0,
        "brier": 0.0,
        "baseline_mae": 0.0,
        "baseline_brier": 0.0,
        "brier_lift": 0.0,
        "n_splits": 0,
        "train_rows": float(len(panel)),
        "test_rows": 0.0,
        "folds": [],
    }
    if panel.empty:
        return insufficient

    ordered = panel.sort_values("timestamp_hour").reset_index(drop=True)
    # Fold on distinct timestamps; TimeSeriesSplit needs at least two folds.
    splits = min(n_splits, ordered["timestamp_hour"].nunique() - 1)
    if splits < 2:
        return insufficient

    folds = [_score_fold(train, test) for train, test in _rolling_folds(ordered, splits)]

    def _mean(key: str) -> float:
        return sum(fold[key] for fold in folds) / len(folds)

    brier = _mean("brier")
    baseline_brier = _mean("baseline_brier")
    return {
        "mae": _mean("mae"),
        "brier": brier,
        "baseline_mae": _mean("baseline_mae"),
        "baseline_brier": baseline_brier,
        # Positive lift = model beats the constant base-rate predictor's Brier.
        "brier_lift": baseline_brier - brier,
        "n_splits": len(folds),
        # Largest expanding window trained / total out-of-sample rows scored.
        "train_rows": folds[-1]["train_rows"],
        "test_rows": float(sum(fold["test_rows"] for fold in folds)),
        "folds": folds,
    }
