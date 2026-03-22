"""
Telegram Bot
------------
Handles /start command and opens the Mini App via WebApp button.
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from loguru import logger

from backend.config import settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — send Mini App button."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot")


    await update.message.reply_html(
        f"Привет, <b>{user.first_name}</b>! 👋\n\n"
        f"🎓 Бот для просмотра расписания института.\n\n"
        f"Нажми кнопку <b>Расписание</b> в меню слева, чтобы открыть расписание."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 Доступные команды:\n"
        "/start — открыть расписание\n"
        "/help — эта справка"
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle data sent back from the Mini App (optional)."""
    data = update.effective_message.web_app_data.data
    logger.info(f"WebApp data received: {data}")
    await update.message.reply_text(f"Получены данные из Mini App: {data}")


def run_bot():
    """Start the Telegram bot (polling mode)."""
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "your_bot_token":
        logger.error("BOT_TOKEN not configured! Set it in .env file")
        return

    logging.basicConfig(level=logging.WARNING)

    app = Application.builder().token(settings.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data)
    )

    logger.info("🤖 Bot started (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
