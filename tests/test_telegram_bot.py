import pandas as pd

from airalert_planner.planner import SAFETY_DISCLAIMER
from airalert_planner.risk import fit_risk_model
from airalert_planner.telegram_bot import HELP_TEXT, handle_risk, handle_trip


def _model():
    """A small fitted model so handlers exercise the real planner delegation."""
    rows = []
    for day in range(4):
        for hour in range(24):
            rows.append(
                {
                    "region": "Kyiv",
                    "timestamp_hour": pd.Timestamp("2026-06-01T00:00:00Z")
                    + pd.Timedelta(days=day, hours=hour),
                    "weekday": day,
                    "hour": hour,
                    "alert_active": 1 if hour >= 20 else 0,
                }
            )
    return fit_risk_model(pd.DataFrame(rows))


def test_handle_risk_delegates_to_planner_window_summary():
    # A valid request must return the planner's own window summary verbatim
    # (Region header + safety disclaimer), proving the bot reuses planner logic
    # rather than reformatting it.
    text = handle_risk(_model(), ["Kyiv", "2026-06-26", "18", "22"])

    assert "Region: Kyiv" in text
    assert SAFETY_DISCLAIMER in text


def test_handle_risk_missing_args_returns_usage_not_crash():
    # Telegram users send malformed commands constantly; a missing argument must
    # produce a usage hint, never an unhandled exception.
    text = handle_risk(_model(), ["Kyiv"])

    assert "Usage: /risk" in text
    assert "Region: Kyiv" not in text


def test_handle_risk_empty_args_returns_usage():
    # A bare "/risk" yields an empty arg list; that is the usage path, not a crash.
    text = handle_risk(_model(), [])

    assert "Usage: /risk" in text


def test_handle_risk_invalid_window_returns_usage_not_crash():
    # from_hour >= to_hour makes summarize_window raise ValueError; the wrapper
    # must catch it and guide the user instead of propagating.
    text = handle_risk(_model(), ["Kyiv", "2026-06-26", "22", "18"])

    assert "/risk" in text
    assert "Region: Kyiv" not in text


def test_handle_trip_delegates_to_planner_trip_summary():
    # /trip must expose the planner's trip sketch for the variadic region tail.
    text = handle_trip(_model(), ["2026-06-26", "Kyiv", "Lviv"])

    assert "Kyiv" in text
    assert "Lviv" in text
    assert SAFETY_DISCLAIMER in text


def test_handle_trip_requires_at_least_one_region():
    # A date with no regions can't be summarized; return the usage path, not an
    # accidental planner success (so the disclaimer must be absent).
    text = handle_trip(_model(), ["2026-06-26"])

    assert "Usage: /trip" in text
    assert SAFETY_DISCLAIMER not in text


def test_handlers_tolerate_none_args():
    # A bare command can hand the wrapper a falsy/None args object; both handlers
    # must treat it as "no arguments" and return usage, never raise.
    assert "Usage: /risk" in handle_risk(_model(), None)
    assert "Usage: /trip" in handle_trip(_model(), None)


def test_help_text_lists_both_product_commands():
    # The help/start text is the bot's front door: it must advertise both
    # planning surfaces so a new user can self-serve.
    assert "/risk" in HELP_TEXT
    assert "/trip" in HELP_TEXT
