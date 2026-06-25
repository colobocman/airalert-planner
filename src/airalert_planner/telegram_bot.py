"""Optional thin Telegram adapter.

This module owns NO planning logic. Each command parses arguments, delegates to
``planner`` (the same functions the CLI uses), and returns the planner's text.
The reply-building functions are pure and telegram-free so they can be tested
without the optional ``python-telegram-bot`` dependency installed.
"""

from __future__ import annotations

import os

from .cli import build_model
from .planner import summarize_trip, summarize_window
from .risk import RiskModel

HELP_TEXT = (
    "AirAlert Planner — historical air-raid risk for trip, event, and shift planning.\n"
    "Historical support only; always follow official alerts and local guidance.\n"
    "\n"
    "Commands:\n"
    "/risk <region> <date> <from_hour> <to_hour>\n"
    "    e.g. /risk Kyiv 2026-06-26 18 22\n"
    "/trip <date> <region> [region ...]\n"
    "    e.g. /trip 2026-06-26 Kyiv Lviv\n"
    "/help — show this message\n"
    "\n"
    "Hours are 0-24 in Europe/Kyiv local time; regions are single words."
)

_RISK_USAGE = "Usage: /risk <region> <date> <from_hour> <to_hour>\nExample: /risk Kyiv 2026-06-26 18 22"
_TRIP_USAGE = "Usage: /trip <date> <region> [region ...]\nExample: /trip 2026-06-26 Kyiv Lviv"


def handle_risk(model: RiskModel, args: list[str] | None) -> str:
    """Parse a /risk command, delegate to the planner, return reply text.

    Pure and telegram-free: a malformed or empty request (``args`` may be None
    for a bare command) yields a usage hint instead of raising, so the bot never
    crashes on user input.
    """
    args = args or []
    try:
        region, date, from_hour, to_hour = args[0], args[1], int(args[2]), int(args[3])
        return summarize_window(model, region, date, from_hour, to_hour).to_text()
    except (IndexError, ValueError) as exc:
        return f"Could not read that request ({exc}).\n{_RISK_USAGE}"


def handle_trip(model: RiskModel, args: list[str] | None) -> str:
    """Parse a /trip command, delegate to the planner, return reply text.

    The date comes first so the variadic region list is unambiguous. ``args``
    may be None for a bare command; treat it as no arguments.
    """
    args = args or []
    try:
        date, regions = args[0], list(args[1:])
        return summarize_trip(model, regions, date)
    except (IndexError, ValueError) as exc:
        return f"Could not read that request ({exc}).\n{_TRIP_USAGE}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Optional Telegram wrapper for AirAlert Planner")
    parser.add_argument("--input", default="data/sample_alerts.csv")
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN before starting the bot")

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes
    except ImportError as exc:
        raise SystemExit("Install bot dependencies with: pip install -e '.[bot]'") from exc

    _, _, model = build_model(args.input)

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(HELP_TEXT)

    async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(handle_risk(model, context.args))

    async def trip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(handle_trip(model, context.args))

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", help_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("risk", risk_cmd))
    app.add_handler(CommandHandler("trip", trip_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
