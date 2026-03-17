"""
CORE — app/core/dependencies.py
────────────────────────────────────────────────────────────────────────────────
LESSON: This is the Composition Root — the ONLY place in the entire app
where concrete implementations are wired to interfaces.

Think of it like a factory or IoC container (Spring @Bean, Angular providers).
Every piece of the app is assembled HERE and injected everywhere else.

WHY centralise this?
  - To swap InMemoryMetricRepository → RedisMetricRepository, change ONE line
  - FastAPI's Depends() system calls these functions on every request,
    returning the same singleton instances (we use module-level singletons)
  - Unit tests can override these with fakes using app.dependency_overrides

Interview answer: "I used constructor injection throughout and centralised
wiring in a composition root so the system is fully testable and swappable."
"""

from __future__ import annotations

from functools import lru_cache

from app.application.use_cases.detect_anomalies import (
    AcknowledgeAnomalyUseCase,
    DetectAnomaliesUseCase,
    ResolveAlertUseCase,
)
from app.application.use_cases.get_metrics import GetMetricsUseCase, GetSingleMetricUseCase
from app.domain.repositories.anomaly_repository import IAnomalyRepository, IAlertRepository
from app.domain.repositories.metric_repository import IMetricRepository
from app.domain.services.anomaly_detection_service import AnomalyDetectionService
from app.infrastructure.ml.isolation_forest_detector import IsolationForestDetector
from app.infrastructure.repositories.in_memory_anomaly_repo import (
    InMemoryAlertRepository,
    InMemoryAnomalyRepository,
)
from app.infrastructure.repositories.in_memory_metric_repo import InMemoryMetricRepository
from app.infrastructure.websocket.connection_manager import ConnectionManager


# ── Singletons (module-level, created once on startup) ────────────────────────
# lru_cache(maxsize=1) ensures only one instance is ever created,
# making these effectively application-scoped singletons.

@lru_cache(maxsize=1)
def get_connection_manager() -> ConnectionManager:
    return ConnectionManager()


@lru_cache(maxsize=1)
def get_metric_repo() -> IMetricRepository:
    return InMemoryMetricRepository()


@lru_cache(maxsize=1)
def get_anomaly_repo() -> IAnomalyRepository:
    return InMemoryAnomalyRepository()


@lru_cache(maxsize=1)
def get_alert_repo() -> IAlertRepository:
    return InMemoryAlertRepository()


@lru_cache(maxsize=1)
def get_detection_service() -> AnomalyDetectionService:
    detector = IsolationForestDetector()
    return AnomalyDetectionService(detector=detector)


# ── Use Case Factories (called by FastAPI Depends) ────────────────────────────

def get_metrics_use_case() -> GetMetricsUseCase:
    return GetMetricsUseCase(metric_repo=get_metric_repo())


def get_single_metric_use_case() -> GetSingleMetricUseCase:
    return GetSingleMetricUseCase(metric_repo=get_metric_repo())


def get_detect_anomalies_use_case() -> DetectAnomaliesUseCase:
    return DetectAnomaliesUseCase(
        metric_repo=get_metric_repo(),
        anomaly_repo=get_anomaly_repo(),
        alert_repo=get_alert_repo(),
        detection_service=get_detection_service(),
        broadcast_fn=get_connection_manager().broadcast,
    )


def get_acknowledge_anomaly_use_case() -> AcknowledgeAnomalyUseCase:
    return AcknowledgeAnomalyUseCase(anomaly_repo=get_anomaly_repo())


def get_resolve_alert_use_case() -> ResolveAlertUseCase:
    return ResolveAlertUseCase(alert_repo=get_alert_repo())
