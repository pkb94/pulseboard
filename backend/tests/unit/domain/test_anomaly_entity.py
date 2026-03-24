"""Unit tests for Anomaly and AnomalySeverity domain entities."""

import pytest
from datetime import datetime

from app.domain.entities.anomaly import Anomaly, AnomalySeverity
from app.domain.entities.metric import MetricName


def _make_anomaly(**overrides) -> Anomaly:
    defaults = dict(
        metric=MetricName.CPU_USAGE,
        observed_value=95.0,
        expected_range=(20.0, 80.0),
        confidence=0.9,
        severity=AnomalySeverity.HIGH,
        description="Test anomaly",
    )
    defaults.update(overrides)
    return Anomaly(**defaults)


# ── AnomalySeverity ────────────────────────────────────────────────────────────

class TestAnomalySeverity:
    def test_critical_high_confidence_and_magnitude(self):
        result = AnomalySeverity.from_confidence(0.95, 3.0)
        assert result == AnomalySeverity.CRITICAL

    def test_high_from_confidence_alone(self):
        result = AnomalySeverity.from_confidence(0.8, 1.0)
        assert result == AnomalySeverity.HIGH

    def test_high_from_magnitude_alone(self):
        result = AnomalySeverity.from_confidence(0.3, 1.6)
        assert result == AnomalySeverity.HIGH

    def test_medium_from_confidence(self):
        result = AnomalySeverity.from_confidence(0.6, 1.0)
        assert result == AnomalySeverity.MEDIUM

    def test_medium_from_magnitude(self):
        result = AnomalySeverity.from_confidence(0.3, 1.3)
        assert result == AnomalySeverity.MEDIUM

    def test_low_default_below_all_thresholds(self):
        result = AnomalySeverity.from_confidence(0.2, 1.0)
        assert result == AnomalySeverity.LOW

    def test_critical_requires_both_conditions(self):
        # confidence meets threshold but magnitude does not → HIGH, not CRITICAL
        result = AnomalySeverity.from_confidence(0.95, 1.0)
        assert result == AnomalySeverity.HIGH


# ── Anomaly ────────────────────────────────────────────────────────────────────

class TestAnomaly:
    def test_defaults_on_creation(self):
        a = _make_anomaly()
        assert a.acknowledged is False
        assert a.acknowledged_at is None
        assert a.id is not None

    def test_each_anomaly_gets_unique_id(self):
        a1 = _make_anomaly()
        a2 = _make_anomaly()
        assert a1.id != a2.id

    def test_acknowledge_sets_flags(self):
        a = _make_anomaly()
        a.acknowledge()
        assert a.acknowledged is True
        assert a.acknowledged_at is not None

    def test_acknowledge_sets_timestamp_close_to_now(self):
        before = datetime.utcnow()
        a = _make_anomaly()
        a.acknowledge()
        after = datetime.utcnow()
        assert before <= a.acknowledged_at <= after

    def test_double_acknowledge_raises(self):
        a = _make_anomaly()
        a.acknowledge()
        with pytest.raises(ValueError, match="already acknowledged"):
            a.acknowledge()

    def test_deviation_pct_calculation(self):
        # observed=120, expected=(0, 80) → 120/80 = 1.5
        a = _make_anomaly(observed_value=120.0, expected_range=(0.0, 80.0))
        assert a.deviation_pct == pytest.approx(1.5)

    def test_deviation_pct_zero_when_upper_is_zero(self):
        a = _make_anomaly(observed_value=10.0, expected_range=(0.0, 0.0))
        assert a.deviation_pct == 0.0
