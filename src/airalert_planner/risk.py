from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import brier_score_loss, mean_absolute_error


@dataclass(frozen=True)
class RiskModel:
    by_region_weekday_hour: pd.DataFrame
    by_region_hour: pd.DataFrame
    by_global_hour: pd.DataFrame
    global_mean: float

    def predict_one(self, region: str, weekday: int, hour: int) -> float:
        exact = self.by_region_weekday_hour
        mask = (exact.region == region) & (exact.weekday == weekday) & (exact.hour == hour)
        if mask.any():
            return float(exact.loc[mask, "risk"].iloc[0])

        region_hour = self.by_region_hour
        mask = (region_hour.region == region) & (region_hour.hour == hour)
        if mask.any():
            return float(region_hour.loc[mask, "risk"].iloc[0])

        global_hour = self.by_global_hour
        mask = global_hour.hour == hour
        if mask.any():
            return float(global_hour.loc[mask, "risk"].iloc[0])

        return float(self.global_mean)


def fit_risk_model(panel: pd.DataFrame) -> RiskModel:
    if panel.empty:
        empty = pd.DataFrame(columns=["region", "weekday", "hour", "risk"])
        return RiskModel(empty, pd.DataFrame(columns=["region", "hour", "risk"]), pd.DataFrame(columns=["hour", "risk"]), 0.0)

    by_region_weekday_hour = (
        panel.groupby(["region", "weekday", "hour"], as_index=False)["alert_active"].mean().rename(columns={"alert_active": "risk"})
    )
    by_region_hour = panel.groupby(["region", "hour"], as_index=False)["alert_active"].mean().rename(columns={"alert_active": "risk"})
    by_global_hour = panel.groupby(["hour"], as_index=False)["alert_active"].mean().rename(columns={"alert_active": "risk"})
    global_mean = float(panel["alert_active"].mean())
    return RiskModel(by_region_weekday_hour, by_region_hour, by_global_hour, global_mean)


def risk_table(model: RiskModel, regions: list[str]) -> pd.DataFrame:
    rows = []
    for region in regions:
        for weekday in range(7):
            for hour in range(24):
                rows.append({"region": region, "weekday": weekday, "hour": hour, "risk": model.predict_one(region, weekday, hour)})
    return pd.DataFrame(rows)


def chronological_validation(panel: pd.DataFrame, split_ratio: float = 0.8) -> dict[str, float]:
    """Validate using earlier hours for training and later hours for evaluation."""
    if panel.empty or len(panel) < 4:
        return {"mae": 0.0, "brier": 0.0, "train_rows": float(len(panel)), "test_rows": 0.0}

    ordered = panel.sort_values("timestamp_hour")
    split_idx = max(1, min(len(ordered) - 1, int(len(ordered) * split_ratio)))
    train = ordered.iloc[:split_idx]
    test = ordered.iloc[split_idx:]
    model = fit_risk_model(train)
    preds = [model.predict_one(row.region, int(row.weekday), int(row.hour)) for row in test.itertuples(index=False)]
    y = test["alert_active"].astype(float).to_list()
    return {
        "mae": float(mean_absolute_error(y, preds)),
        "brier": float(brier_score_loss(y, preds)),
        "train_rows": float(len(train)),
        "test_rows": float(len(test)),
    }
