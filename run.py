import asyncio
import threading
import uvicorn
from loguru import logger

from backend.config import settings
from backend.main import app


def run_api():
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="warning")


def run_bot_in_thread():
    async def _bot():
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from bot import start, help_command, handle_webapp_data

        application = Application.builder().token(settings.BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(
            MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data)
        )
        logger.info("🤖 Bot started (polling)")
        async with application:
            await application.start()
            await application.updater.start_polling(allowed_updates=["message", "callback_query"])
            await asyncio.Event().wait()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_bot())


if __name__ == "__main__":
    logger.info(f"🚀 Starting on {settings.HOST}:{settings.PORT}")

    if settings.BOT_TOKEN and settings.BOT_TOKEN != "your_bot_token":
        bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
        bot_thread.start()

    logger.info(f"✅ API started at http://{settings.HOST}:{settings.PORT}")
    run_api()
