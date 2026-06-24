from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import brier_score_loss, mean_absolute_error

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


def chronological_validation(panel: pd.DataFrame, split_ratio: float = 0.8) -> dict[str, float]:
    """Validate using earlier hours for training and later hours for evaluation."""
    if panel.empty or len(panel) < 4:
        return {
            "mae": 0.0,
            "brier": 0.0,
            "baseline_mae": 0.0,
            "baseline_brier": 0.0,
            "train_rows": float(len(panel)),
            "test_rows": 0.0,
        }

    ordered = panel.sort_values("timestamp_hour")
    split_idx = max(1, min(len(ordered) - 1, int(len(ordered) * split_ratio)))
    train = ordered.iloc[:split_idx]
    test = ordered.iloc[split_idx:]
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
