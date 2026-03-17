"""
LAYER 4 — PRESENTATION — app/presentation/api/routes/health.py
"""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Kubernetes liveness probe endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


@router.get("/api/health/system")
async def system_health() -> dict:
    """Returns aggregated system health — expanded in future with real checks."""
    return {
        "status": "operational",
        "uptime_pct": 99.95,
        "services": [
            {"name": "metric-simulator", "status": "operational", "latency_ms": 1},
            {"name": "anomaly-detector", "status": "operational", "latency_ms": 12},
            {"name": "websocket-hub",    "status": "operational", "latency_ms": 0},
        ],
    }
