from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .risk import RiskModel

SAFETY_DISCLAIMER = "Historical planning support only. Always follow official alerts and local security guidance."

# Below this many matching historical hours, an estimate is flagged low-confidence.
LOW_CONFIDENCE_SUPPORT = 3
# Risk spread under this is treated as no meaningful difference across the window.
FLAT_RISK_EPSILON = 1e-9


@dataclass(frozen=True)
class WindowRiskSummary:
    region: str
    date: str
    from_hour: int
    to_hour: int
    average_risk: float
    lowest_risk_hour: int
    highest_risk_hour: int
    rows: list[dict]

    def to_text(self) -> str:
        risks = [row["risk"] for row in self.rows]
        flat = max(risks) - min(risks) < FLAT_RISK_EPSILON
        lines = [
            f"Region: {self.region}",
            f"Window: {self.date} {self.from_hour:02d}:00-{self.to_hour:02d}:00 (Europe/Kyiv)",
            f"Average historical risk: {self.average_risk:.2f}",
        ]
        if flat:
            lines.append("No material difference in historical risk across this window.")
        else:
            lines.append(f"Relatively lower-risk hour: {self.lowest_risk_hour:02d}:00")
            lines.append(f"Relatively higher-risk hour: {self.highest_risk_hour:02d}:00")

        max_support = max(row["support"] for row in self.rows)
        if max_support < LOW_CONFIDENCE_SUPPORT:
            lines.append(
                f"Low confidence: at most {max_support} matching past hour(s) of history for this window."
            )

        lines.extend(["", "Hourly profile:"])
        for row in self.rows:
            lines.append(f"- {row['hour']:02d}:00 risk={row['risk']:.2f} (n={row['support']})")
        lines.extend(
            [
                "",
                "risk = share of matching past hours that were under an alert (0 = never, 1 = always); n = matching hours observed.",
                SAFETY_DISCLAIMER,
            ]
        )
        return "\n".join(lines)


def summarize_window(model: RiskModel, region: str, date: str, from_hour: int, to_hour: int) -> WindowRiskSummary:
    if not 0 <= from_hour <= 23 or not 1 <= to_hour <= 24 or from_hour >= to_hour:
        raise ValueError("Expected 0 <= from_hour < to_hour <= 24")
    weekday = pd.Timestamp(date).weekday()
    rows = [
        {
            "hour": hour,
            "risk": model.predict_one(region, weekday, hour),
            "support": model.support_one(region, weekday, hour),
        }
        for hour in range(from_hour, to_hour)
    ]
    lowest = min(rows, key=lambda row: row["risk"])
    highest = max(rows, key=lambda row: row["risk"])
    avg = sum(row["risk"] for row in rows) / len(rows)
    return WindowRiskSummary(region, date, from_hour, to_hour, avg, int(lowest["hour"]), int(highest["hour"]), rows)


def summarize_trip(model: RiskModel, regions: list[str], date: str) -> str:
    if not regions:
        raise ValueError("At least one region is required")
    lines = [f"Route-like regional risk sketch for {date}", ""]
    for region in regions:
        summary = summarize_window(model, region=region, date=date, from_hour=8, to_hour=22)
        lines.append(f"- {region}: avg daytime risk={summary.average_risk:.2f}, lower around {summary.lowest_risk_hour:02d}:00")
    lines.extend(["", "This is region-sequence planning, not geospatial routing.", SAFETY_DISCLAIMER])
    return "\n".join(lines)
