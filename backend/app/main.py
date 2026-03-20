"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables, migrate_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting up...")

    # Create DB tables + run migrations
    await create_tables()
    await migrate_db()
    logger.info("Database tables ready")

    # Start scheduler
    from app.scheduler import scheduler as sched
    sched.start(None)
    await sched.load_jobs_from_db()

    # Start Telegram bot
    from app.telegram.bot import start_bot
    await start_bot()

    logger.info("Startup complete")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down...")
    from app.telegram.bot import stop_bot
    await stop_bot()

    from app.scheduler import scheduler as sched
    sched.stop()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Agent Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api import agents, runs, findings  # noqa: E402
app.include_router(agents.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(findings.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    from app.scheduler.scheduler import list_all_jobs
    return {
        "status": "ok",
        "environment": settings.environment,
        "scheduled_jobs": len(list_all_jobs()),
    }
