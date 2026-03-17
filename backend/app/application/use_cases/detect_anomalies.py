"""
LAYER 2 — USE CASE — app/application/use_cases/detect_anomalies.py
────────────────────────────────────────────────────────────────────
LESSON: This use case orchestrates the anomaly detection PIPELINE:

  1. Receive a new metric point (event-driven, called by the simulator)
  2. Fetch the full series from the repo
  3. Call the domain service (which calls the ML detector)
  4. If anomaly found: persist it, create an alert, broadcast via WebSocket

This is the most complex use case — it touches 3 repositories
and 1 domain service. Notice: none of that complexity leaks to the API.
"""

from __future__ import annotations

from typing import Callable, Awaitable

from app.application.dto.anomaly_dto import AlertDTO, AnomalyDTO
from app.domain.entities.alert import Alert
from app.domain.entities.metric import MetricName, MetricPoint
from app.domain.repositories.anomaly_repository import IAnomalyRepository, IAlertRepository
from app.domain.repositories.metric_repository import IMetricRepository
from app.domain.services.anomaly_detection_service import AnomalyDetectionService

# Type alias for the WebSocket broadcast callback
BroadcastFn = Callable[[dict], Awaitable[None]]


class DetectAnomaliesUseCase:
    """
    Processes a new data point and runs anomaly detection.
    The broadcast_fn is injected so this use case doesn't import
    any WebSocket library — it just calls a callback.
    """

    def __init__(
        self,
        metric_repo: IMetricRepository,
        anomaly_repo: IAnomalyRepository,
        alert_repo: IAlertRepository,
        detection_service: AnomalyDetectionService,
        broadcast_fn: BroadcastFn,
    ) -> None:
        self._metrics = metric_repo
        self._anomalies = anomaly_repo
        self._alerts = alert_repo
        self._detection = detection_service
        self._broadcast = broadcast_fn

    async def execute(self, metric: MetricName, value: float) -> AnomalyDTO | None:
        from datetime import datetime
        from app.domain.entities.metric import MetricPoint

        # Step 1: Persist the new data point
        point = MetricPoint(metric=metric, value=value, timestamp=datetime.utcnow())
        await self._metrics.save_point(point)

        # Step 2: Fetch series context for the ML model
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(minutes=30)
        series = await self._metrics.get_series(metric, since)

        # Step 3: Ask domain service to evaluate (applies business rules)
        anomaly = self._detection.evaluate(series)

        if anomaly is None:
            return None

        # Step 4: Persist the anomaly
        await self._anomalies.save(anomaly)

        # Step 5: Create and persist an Alert
        alert = Alert(
            metric=anomaly.metric,
            title=f"{anomaly.severity.value.upper()} anomaly: {anomaly.metric.value}",
            message=anomaly.description,
            severity=anomaly.severity,
            anomaly_id=anomaly.id,
        )
        await self._alerts.save(alert)

        # Step 6: Broadcast to all WebSocket clients (non-blocking)
        await self._broadcast({
            "type": "anomaly_detected",
            "payload": AnomalyDTO.from_entity(anomaly).model_dump(mode="json"),
            "alert": AlertDTO.from_entity(alert).model_dump(mode="json"),
        })

        return AnomalyDTO.from_entity(anomaly)


class AcknowledgeAnomalyUseCase:
    """Single-purpose use case for acknowledging an anomaly."""

    def __init__(self, anomaly_repo: IAnomalyRepository) -> None:
        self._repo = anomaly_repo

    async def execute(self, anomaly_id: str) -> AnomalyDTO:
        anomaly = await self._repo.acknowledge(anomaly_id)
        return AnomalyDTO.from_entity(anomaly)


class ResolveAlertUseCase:
    """Single-purpose use case for resolving an alert."""

    def __init__(self, alert_repo: IAlertRepository) -> None:
        self._repo = alert_repo

    async def execute(self, alert_id: str) -> AlertDTO:
        alert = await self._repo.get_by_id(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} not found")
        alert.resolve()          # Domain method — state machine validates transition
        await self._repo.update(alert)
        return AlertDTO.from_entity(alert)
