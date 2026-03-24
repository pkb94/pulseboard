"""Unit tests for Alert domain entity and its lifecycle."""

import pytest

from app.domain.entities.alert import Alert, AlertStatus
from app.domain.entities.anomaly import AnomalySeverity
from app.domain.entities.metric import MetricName


def _make_alert(**overrides) -> Alert:
    defaults = dict(
        metric=MetricName.ERROR_RATE,
        title="High error rate",
        message="Error rate spiked",
        severity=AnomalySeverity.HIGH,
        anomaly_id="test-anomaly-id",
    )
    defaults.update(overrides)
    return Alert(**defaults)


class TestAlert:
    def test_initial_status_is_active(self):
        alert = _make_alert()
        assert alert.status == AlertStatus.ACTIVE

    def test_is_active_property_true_initially(self):
        alert = _make_alert()
        assert alert.is_active is True

    def test_acknowledge_moves_to_acknowledged(self):
        alert = _make_alert()
        alert.acknowledge()
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.is_active is False

    def test_acknowledge_non_active_alert_raises(self):
        alert = _make_alert()
        alert.status = AlertStatus.RESOLVED
        with pytest.raises(ValueError, match="Cannot acknowledge"):
            alert.acknowledge()

    def test_resolve_moves_to_resolved(self):
        alert = _make_alert()
        alert.resolve()
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None

    def test_resolve_sets_resolved_at_timestamp(self):
        from datetime import datetime
        before = datetime.utcnow()
        alert = _make_alert()
        alert.resolve()
        after = datetime.utcnow()
        assert before <= alert.resolved_at <= after

    def test_resolve_already_resolved_raises(self):
        alert = _make_alert()
        alert.resolve()
        with pytest.raises(ValueError, match="already resolved"):
            alert.resolve()

    def test_can_resolve_acknowledged_alert(self):
        alert = _make_alert()
        alert.acknowledge()
        alert.resolve()
        assert alert.status == AlertStatus.RESOLVED

    def test_each_alert_gets_unique_id(self):
        a1 = _make_alert()
        a2 = _make_alert()
        assert a1.id != a2.id

    def test_duration_seconds_is_non_negative(self):
        alert = _make_alert()
        assert alert.duration_seconds >= 0.0

    def test_duration_seconds_after_resolve(self):
        import time
        alert = _make_alert()
        time.sleep(0.05)
        alert.resolve()
        assert alert.duration_seconds >= 0.05
