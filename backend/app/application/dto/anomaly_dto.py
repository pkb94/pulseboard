"""
LAYER 2 — APPLICATION DTO — app/application/dto/anomaly_dto.py
"""

from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from app.domain.entities.anomaly import Anomaly, AnomalySeverity
from app.domain.entities.alert import Alert, AlertStatus
from app.domain.entities.metric import MetricName


class AnomalyDTO(BaseModel):
    id: str
    metric: MetricName
    observed_value: float
    expected_range: tuple[float, float]
    confidence: float
    severity: AnomalySeverity
    description: str
    detected_at: datetime
    acknowledged: bool

    @classmethod
    def from_entity(cls, a: Anomaly) -> "AnomalyDTO":
        return cls(
            id=a.id,
            metric=a.metric,
            observed_value=a.observed_value,
            expected_range=a.expected_range,
            confidence=round(a.confidence, 3),
            severity=a.severity,
            description=a.description,
            detected_at=a.detected_at,
            acknowledged=a.acknowledged,
        )


class AlertDTO(BaseModel):
    id: str
    metric: MetricName
    title: str
    message: str
    severity: AnomalySeverity
    status: AlertStatus
    anomaly_id: str
    triggered_at: datetime
    resolved_at: datetime | None = None
    duration_seconds: float

    @classmethod
    def from_entity(cls, a: Alert) -> "AlertDTO":
        return cls(
            id=a.id,
            metric=a.metric,
            title=a.title,
            message=a.message,
            severity=a.severity,
            status=a.status,
            anomaly_id=a.anomaly_id,
            triggered_at=a.triggered_at,
            resolved_at=a.resolved_at,
            duration_seconds=round(a.duration_seconds, 1),
        )
