"""
LAYER 1 — DOMAIN SERVICE — app/domain/services/anomaly_detection_service.py
─────────────────────────────────────────────────────────────────────────────
LESSON: Domain Services contain business logic that doesn't naturally
belong to a single Entity.

The DETECTION ALGORITHM (Isolation Forest, Z-score) is infrastructure.
But the BUSINESS RULES around detection live here:

  "If confidence > 0.9 AND metric is error_rate → always CRITICAL"
  "Ignore anomalies during known maintenance windows"
  "Deduplicate: don't re-alert on the same metric within 5 minutes"

This is the difference between:
  - Infrastructure concern: "the math says score = 0.87"
  - Domain concern: "0.87 on error_rate means CRITICAL, alert the team"

The domain service receives an abstract detector via the constructor
(Dependency Injection) — it never imports the ML model directly.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Protocol

from app.domain.entities.anomaly import Anomaly, AnomalySeverity
from app.domain.entities.metric import MetricName, MetricSeries


class IAnomalyDetector(Protocol):
    """
    Protocol (structural typing) — Python's duck-typed interface.
    Any class with a detect() method matching this signature works.
    No inheritance required. This is the "ports" side of ports & adapters.
    """

    def detect(self, series: MetricSeries) -> tuple[bool, float, tuple[float, float]]:
        """
        Returns: (is_anomaly, confidence, expected_range)
        """
        ...


class AnomalyDetectionService:
    """
    Domain service that orchestrates anomaly detection with business rules.
    Receives the detector via constructor injection — testable with a stub.
    """

    # BUSINESS RULE: Don't re-alert on the same metric within this window
    DEDUP_WINDOW = timedelta(minutes=5)

    def __init__(self, detector: IAnomalyDetector) -> None:
        self._detector = detector
        # Track last anomaly time per metric for deduplication
        self._last_anomaly: dict[MetricName, datetime] = {}

    def evaluate(self, series: MetricSeries) -> Optional[Anomaly]:
        """
        Core domain logic:
        1. Run the ML detector (infrastructure concern, abstracted)
        2. Apply deduplication business rule
        3. Apply severity business rules
        4. Create and return an Anomaly entity (or None if all clear)
        """
        is_anomaly, confidence, expected_range = self._detector.detect(series)

        if not is_anomaly:
            return None

        # BUSINESS RULE: Deduplication — suppress noisy alerts
        last = self._last_anomaly.get(series.metric)
        if last and (datetime.utcnow() - last) < self.DEDUP_WINDOW:
            return None  # Too soon since last anomaly on this metric

        current_value = series.current_value or 0.0
        _, upper = expected_range
        magnitude = current_value / upper if upper > 0 else 1.0

        # BUSINESS RULE: Override severity for critical business metrics
        severity = AnomalySeverity.from_confidence(confidence, magnitude)
        if series.metric == MetricName.ERROR_RATE and confidence > 0.8:
            severity = AnomalySeverity.CRITICAL  # Error rate anomalies are always critical

        description = self._build_description(series.metric, current_value, expected_range, severity)

        anomaly = Anomaly(
            metric=series.metric,
            observed_value=current_value,
            expected_range=expected_range,
            confidence=confidence,
            severity=severity,
            description=description,
        )

        self._last_anomaly[series.metric] = anomaly.detected_at
        return anomaly

    @staticmethod
    def _build_description(
        metric: MetricName,
        value: float,
        expected_range: tuple[float, float],
        severity: AnomalySeverity,
    ) -> str:
        low, high = expected_range
        return (
            f"{metric.value} spiked to {value:.2f} "
            f"(expected {low:.2f}–{high:.2f}). "
            f"Severity: {severity.value.upper()}"
        )
