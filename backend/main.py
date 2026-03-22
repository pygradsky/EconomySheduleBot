"""
Main Application Entry Point
-----------------------------
FastAPI app + static file serving for Mini App frontend.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from backend.config import settings
from backend.api.routes import router
from backend.api.schedule_service import schedule_service

logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    enqueue=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Schedule Bot API")
    logger.info(f"Data directory: {settings.data_path.resolve()}")
    await schedule_service.load_all()
    logger.info("✅ All schedules loaded")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Institute Schedule API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index = frontend_dir / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "Frontend not found"}

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        target = frontend_dir / full_path
        if target.exists() and target.is_file():
            return FileResponse(str(target))

        index = frontend_dir / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"error": "Not found"}
