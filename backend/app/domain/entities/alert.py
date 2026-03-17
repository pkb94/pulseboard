"""
LAYER 1 — DOMAIN ENTITIES — app/domain/entities/alert.py
──────────────────────────────────────────────────────────
LESSON: Alerts are the OPERATIONAL RESPONSE to anomalies.
They have a lifecycle: active → acknowledged → resolved.

WHY separate Alert from Anomaly?
  - An anomaly is a DETECTION (passive: "something looks wrong")
  - An alert is an ACTION (active: "notify the on-call team")
  - One anomaly can create multiple alert types (email, Slack, PagerDuty)
  - This maps to real incident management systems (PagerDuty, OpsGenie)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from app.domain.entities.anomaly import AnomalySeverity
from app.domain.entities.metric import MetricName


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    metric: MetricName
    title: str
    message: str
    severity: AnomalySeverity
    anomaly_id: str                          # reference back to the triggering anomaly
    status: AlertStatus = AlertStatus.ACTIVE
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ── Lifecycle state machine ────────────────────────────────────────────
    def acknowledge(self) -> None:
        if self.status != AlertStatus.ACTIVE:
            raise ValueError(f"Cannot acknowledge alert in status: {self.status}")
        self.status = AlertStatus.ACKNOWLEDGED

    def resolve(self) -> None:
        if self.status == AlertStatus.RESOLVED:
            raise ValueError("Alert is already resolved")
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        return self.status == AlertStatus.ACTIVE

    @property
    def duration_seconds(self) -> float:
        """How long has this alert been open?"""
        end = self.resolved_at or datetime.utcnow()
        return (end - self.triggered_at).total_seconds()
