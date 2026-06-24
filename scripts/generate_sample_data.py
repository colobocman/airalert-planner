"""Generate the synthetic sample alert dataset.

The sample must *demonstrate* the product: it carries a deliberate, time-stable
``region + hour`` pattern (heavier at night and through the evening, lighter by
day; some regions far more active than others) plus light noise. That lets the
historical baseline beat a constant base-rate predictor under rolling-origin
validation instead of flagging "low confidence" on a toy.

It is synthetic. It does not represent real alert data. Run from the repo root:

    python scripts/generate_sample_data.py

Output is deterministic (fixed seed) so the committed CSV diffs cleanly.
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEED = 20260624
WEEKS = 8
START = date(2026, 4, 6)  # Monday; Apr-May 2026 is entirely Kyiv summer time (+03:00)
KYIV = timezone(timedelta(hours=3))
OUT = Path(__file__).resolve().parents[1] / "data" / "sample_alerts.csv"

# Diurnal alert-start propensity by local hour: a pronounced night peak and a
# rising evening gradient (18 < 19 < 20 < 21 < 22 < 23) so evening windows are
# genuinely differentiated, with quiet daytime hours.
HOUR_WEIGHT = {
    0: 0.35, 1: 0.33, 2: 0.30, 3: 0.26, 4: 0.20,
    5: 0.10, 6: 0.05, 7: 0.04, 8: 0.04, 9: 0.04, 10: 0.05,
    11: 0.05, 12: 0.05, 13: 0.05, 14: 0.06, 15: 0.07,
    16: 0.10, 17: 0.14,
    18: 0.18, 19: 0.22, 20: 0.27, 21: 0.31, 22: 0.34, 23: 0.35,
}

# Region overall intensity (a second, stable signal dimension on top of hour).
REGION_INTENSITY = {
    "Kharkiv": 1.20,
    "Kyiv": 1.00,
    "Odesa": 0.90,
    "Zhytomyr": 0.70,
    "Rivne": 0.60,
    "Ivano-Frankivsk": 0.40,
    "Lviv": 0.30,
}


def _alert_probability(region: str, hour: int) -> float:
    return min(0.85, HOUR_WEIGHT[hour] * REGION_INTENSITY[region])


def generate_rows() -> list[dict[str, str]]:
    rng = random.Random(SEED)
    rows: list[dict[str, str]] = []
    for day_offset in range(WEEKS * 7):
        day = START + timedelta(days=day_offset)
        for region in REGION_INTENSITY:
            for hour in range(24):
                if rng.random() >= _alert_probability(region, hour):
                    continue
                start = datetime(day.year, day.month, day.day, hour, rng.randint(0, 59), tzinfo=KYIV)
                end = start + timedelta(minutes=rng.randint(30, 120))
                rows.append(
                    {
                        "region": region,
                        "started_at": start.isoformat(),
                        "ended_at": end.isoformat(),
                    }
                )
    rows.sort(key=lambda row: (row["region"], row["started_at"]))
    return rows


def main() -> None:
    rows = generate_rows()
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["region", "started_at", "ended_at"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic alert events to {OUT}")


if __name__ == "__main__":
    main()
