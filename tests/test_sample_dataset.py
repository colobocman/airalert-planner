from pathlib import Path

from airalert_planner.data import load_alert_events
from airalert_planner.features import build_hourly_panel
from airalert_planner.risk import chronological_validation, fit_risk_model

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = str(ROOT / "data" / "sample_alerts.csv")


def _sample_model():
    return fit_risk_model(build_hourly_panel(load_alert_events(SAMPLE).events))


def test_sample_dataset_lets_model_beat_base_rate():
    """The shipped sample must demonstrate the product, not flag low confidence.

    It needs a learnable, time-stable region+hour pattern so the model beats the
    constant base-rate baseline under rolling-origin validation. Otherwise every
    query reads "low confidence" and the MVP looks broken.
    """
    panel = build_hourly_panel(load_alert_events(SAMPLE).events)
    metrics = chronological_validation(panel)

    assert metrics["n_splits"] >= 3
    assert metrics["brier_lift"] > 0.0


def test_sample_dataset_has_sharp_day_night_contrast():
    """Busy regions must read clearly calm by day and clearly busy by night.

    A muddy ~0.15 midday risk for a high-activity region blurs the diurnal story
    the sample exists to demonstrate.
    """
    model = _sample_model()

    for region in ("Kyiv", "Kharkiv"):
        midday = model.predict_one(region, 4, 12)
        night = model.predict_one(region, 4, 2)
        assert midday < 0.08
        assert night > 0.5
        assert night - midday > 0.5


def test_sample_dataset_separates_busy_and_calm_regions():
    """A quiet region (Lviv) must read clearly calmer on average than a busy one
    (Kharkiv), so the regional dimension of the risk scores is demonstrative."""
    panel = build_hourly_panel(load_alert_events(SAMPLE).events)

    by_region = panel.groupby("region")["alert_active"].mean()

    assert by_region["Lviv"] < 0.10
    assert by_region["Kharkiv"] > 3 * by_region["Lviv"]


def test_sample_dataset_has_confident_evening_history_for_kyiv():
    """Kyiv at a typical evening hour must have enough history to be confident.

    The flagship CLI example queries Kyiv 18:00-22:00; that window should rest on
    real observations, not a borrowed global prior.
    """
    model = fit_risk_model(build_hourly_panel(load_alert_events(SAMPLE).events))

    supports = [model.support_one("Kyiv", weekday, 20) for weekday in range(7)]

    assert max(supports) >= 3
