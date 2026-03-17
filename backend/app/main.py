"""
ENTRYPOINT — app/main.py
─────────────────────────
LESSON: The FastAPI app factory pattern.

Keeping app creation in a factory function (create_app) rather than
module-level means tests can create isolated app instances without
the simulator running — critical for clean unit tests.

The lifespan context manager (asynccontextmanager) replaces the old
@app.on_event("startup") pattern. It's more explicit and testable.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.dependencies import get_connection_manager, get_detect_anomalies_use_case
from app.infrastructure.simulator.metric_simulator import MetricSimulator
from app.presentation.api.routes import anomalies, health, metrics, websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan: code before 'yield' runs on startup, after 'yield' on shutdown.
    This is where we start the background simulator and heartbeat tasks.
    """
    logger.info("Starting PulseBoard API...")

    simulator = MetricSimulator(detect_use_case=get_detect_anomalies_use_case())
    manager = get_connection_manager()

    async def heartbeat_loop() -> None:
        while True:
            await asyncio.sleep(settings.heartbeat_interval_seconds)
            await manager.send_heartbeat()

    # Launch background tasks
    sim_task = asyncio.create_task(simulator.start(), name="metric-simulator")
    hb_task = asyncio.create_task(heartbeat_loop(), name="heartbeat")

    logger.info("Simulator and heartbeat tasks started.")
    yield  # App is running — handle requests here

    # Graceful shutdown
    simulator.stop()
    sim_task.cancel()
    hb_task.cancel()
    logger.info("PulseBoard API shut down cleanly.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="AI-powered real-time operations intelligence API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow the Next.js frontend to call this API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(metrics.router)
    app.include_router(anomalies.router)
    app.include_router(health.router)
    app.include_router(websocket.router)

    return app


# Module-level app instance — used by uvicorn
app = create_app()
