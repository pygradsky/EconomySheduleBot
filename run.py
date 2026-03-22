#!/usr/bin/env python3
"""
run.py — Launch FastAPI server + Telegram bot concurrently.
"""

import asyncio
import sys
import threading
import uvicorn
from loguru import logger

from backend.config import settings
from backend.main import app


def run_api():
    """Run FastAPI in a thread."""
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="warning",
    )


def run_bot():
    """Run Telegram bot."""
    try:
        from bot import run_bot as _run_bot
        _run_bot()
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == "__main__":
    logger.info(f"🚀 Starting on {settings.HOST}:{settings.PORT}")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info(f"✅ API started at http://{settings.HOST}:{settings.PORT}")

    # Bot in main thread (if token configured)
    if settings.BOT_TOKEN and settings.BOT_TOKEN != "your_bot_token":
        logger.info("🤖 Starting Telegram bot...")
        run_bot()
    else:
        logger.warning("BOT_TOKEN not set — only API running. Set BOT_TOKEN in .env to enable the bot.")
        # Keep alive
        api_thread.join()
