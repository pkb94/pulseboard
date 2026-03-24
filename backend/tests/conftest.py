import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.core import dependencies
from app.application.use_cases.get_metrics import GetMetricsUseCase, GetSingleMetricUseCase
from app.application.use_cases.detect_anomalies import (
    AcknowledgeAnomalyUseCase,
    ResolveAlertUseCase,
)
from app.infrastructure.repositories.in_memory_metric_repo import InMemoryMetricRepository
from app.infrastructure.repositories.in_memory_anomaly_repo import (
    InMemoryAnomalyRepository,
    InMemoryAlertRepository,
)
from app.presentation.api.routes import health, metrics, anomalies


@pytest.fixture
def metric_repo():
    return InMemoryMetricRepository()


@pytest.fixture
def anomaly_repo():
    return InMemoryAnomalyRepository()


@pytest.fixture
def alert_repo():
    return InMemoryAlertRepository()


@pytest.fixture
async def client(metric_repo, anomaly_repo, alert_repo):
    """Async HTTP test client with isolated in-memory repos and no background simulator."""
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(anomalies.router)

    app.dependency_overrides[dependencies.get_metric_repo] = lambda: metric_repo
    app.dependency_overrides[dependencies.get_anomaly_repo] = lambda: anomaly_repo
    app.dependency_overrides[dependencies.get_alert_repo] = lambda: alert_repo
    app.dependency_overrides[dependencies.get_metrics_use_case] = lambda: GetMetricsUseCase(
        metric_repo=metric_repo
    )
    app.dependency_overrides[dependencies.get_single_metric_use_case] = (
        lambda: GetSingleMetricUseCase(metric_repo=metric_repo)
    )
    app.dependency_overrides[dependencies.get_acknowledge_anomaly_use_case] = (
        lambda: AcknowledgeAnomalyUseCase(anomaly_repo=anomaly_repo)
    )
    app.dependency_overrides[dependencies.get_resolve_alert_use_case] = (
        lambda: ResolveAlertUseCase(alert_repo=alert_repo)
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
