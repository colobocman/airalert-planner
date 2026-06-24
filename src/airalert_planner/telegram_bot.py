from __future__ import annotations

import argparse
import os

from .cli import build_model
from .planner import summarize_window


def main() -> None:
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
        await update.message.reply_text("Commands:\n/risk <region> <date> <from_hour> <to_hour>\nExample: /risk Kyiv 2026-06-26 18 22")

    async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            region, date, from_hour, to_hour = context.args[0], context.args[1], int(context.args[2]), int(context.args[3])
            text = summarize_window(model, region, date, from_hour, to_hour).to_text()
        except Exception as exc:  # noqa: BLE001 - user-facing bot wrapper
            text = f"Could not parse request: {exc}\nUsage: /risk Kyiv 2026-06-26 18 22"
        await update.message.reply_text(text)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("risk", risk_cmd))
    app.run_polling()


if __name__ == "__main__":
    main()
