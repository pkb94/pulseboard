"""
LAYER 1 — DOMAIN ENTITIES — app/domain/entities/anomaly.py
────────────────────────────────────────────────────────────
LESSON: An Anomaly is a domain event — something that HAPPENED
in the system that violates expected behaviour.

Notice: This file has NO idea how anomalies are DETECTED.
Detection is an algorithm (infrastructure concern).
The entity only represents WHAT an anomaly IS, not HOW it's found.

This separation lets us swap the ML algorithm (isolation forest →
Z-score → LLM) without touching this entity at all.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.domain.entities.metric import MetricName


class AnomalySeverity(str, Enum):
    """
    Severity is determined by BUSINESS RULES (e.g., confidence + magnitude),
    not by the ML model score directly. The model gives a raw score;
    the domain decides what "critical" means to this business.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_confidence(cls, confidence: float, magnitude_pct: float) -> "AnomalySeverity":
        """
        BUSINESS RULE: Map ML confidence + deviation magnitude to severity.
        This is a prime example of domain logic that should NOT live in ML code.

        confidence: 0.0–1.0 (how sure the model is it's anomalous)
        magnitude_pct: how far above normal (e.g., 150% = 50% above threshold)
        """
        if confidence >= 0.9 and magnitude_pct >= 2.0:
            return cls.CRITICAL
        if confidence >= 0.75 or magnitude_pct >= 1.5:
            return cls.HIGH
        if confidence >= 0.5 or magnitude_pct >= 1.2:
            return cls.MEDIUM
        return cls.LOW


@dataclass
class Anomaly:
    """
    An anomaly detected in a metric stream.
    id is auto-generated — domain objects manage their own identity.
    """
    metric: MetricName
    observed_value: float
    expected_range: tuple[float, float]      # (lower_bound, upper_bound)
    confidence: float                         # 0.0–1.0
    severity: AnomalySeverity
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    acknowledged: bool = False
    acknowledged_at: datetime | None = None

    def acknowledge(self) -> None:
        """
        Domain method — acknowledging is a business action.
        Validate the state transition here (can't acknowledge twice).
        """
        if self.acknowledged:
            raise ValueError(f"Anomaly {self.id} is already acknowledged")
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()

    @property
    def deviation_pct(self) -> float:
        """How far is the observed value from the expected upper bound?"""
        _, upper = self.expected_range
        if upper == 0:
            return 0.0
        return self.observed_value / upper
