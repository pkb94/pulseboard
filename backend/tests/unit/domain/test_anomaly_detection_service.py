"""Unit tests for AnomalyDetectionService domain service."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.domain.entities.anomaly import AnomalySeverity
from app.domain.entities.metric import MetricName, MetricPoint, MetricSeries
from app.domain.services.anomaly_detection_service import AnomalyDetectionService


def _mock_detector(is_anomaly: bool, confidence: float = 0.85, expected_range=(10.0, 80.0)):
    detector = MagicMock()
    detector.detect.return_value = (is_anomaly, confidence, expected_range)
    return detector


def _make_series(metric: MetricName = MetricName.CPU_USAGE, value: float = 50.0) -> MetricSeries:
    pt = MetricPoint(metric=metric, value=value, timestamp=datetime.utcnow())
    return MetricSeries(metric=metric, points=[pt])


class TestAnomalyDetectionService:
    def test_returns_none_when_no_anomaly_detected(self):
        service = AnomalyDetectionService(detector=_mock_detector(is_anomaly=False))
        result = service.evaluate(_make_series())
        assert result is None

    def test_returns_anomaly_when_detected(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.85)
        )
        result = service.evaluate(_make_series(value=95.0))
        assert result is not None
        assert result.metric == MetricName.CPU_USAGE

    def test_anomaly_carries_correct_confidence(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.92)
        )
        result = service.evaluate(_make_series(value=95.0))
        assert result.confidence == pytest.approx(0.92)

    def test_anomaly_carries_correct_observed_value(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.85)
        )
        result = service.evaluate(_make_series(value=123.0))
        assert result.observed_value == pytest.approx(123.0)

    def test_dedup_suppresses_second_anomaly_within_window(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.85)
        )
        first = service.evaluate(_make_series(value=95.0))
        second = service.evaluate(_make_series(value=99.0))
        assert first is not None
        assert second is None

    def test_dedup_is_per_metric(self):
        """Anomaly on CPU_USAGE should not suppress anomaly on MEMORY_USAGE."""
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.85)
        )
        cpu_anomaly = service.evaluate(_make_series(metric=MetricName.CPU_USAGE, value=95.0))
        mem_anomaly = service.evaluate(_make_series(metric=MetricName.MEMORY_USAGE, value=95.0))
        assert cpu_anomaly is not None
        assert mem_anomaly is not None

    def test_error_rate_elevated_to_critical_with_high_confidence(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.95, expected_range=(0.0, 5.0))
        )
        result = service.evaluate(_make_series(metric=MetricName.ERROR_RATE, value=15.0))
        assert result is not None
        assert result.severity == AnomalySeverity.CRITICAL

    def test_error_rate_not_elevated_with_low_confidence(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.6, expected_range=(0.0, 5.0))
        )
        result = service.evaluate(_make_series(metric=MetricName.ERROR_RATE, value=8.0))
        assert result is not None
        assert result.severity != AnomalySeverity.CRITICAL

    def test_description_contains_metric_name(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.7, expected_range=(10.0, 80.0))
        )
        result = service.evaluate(_make_series(metric=MetricName.LATENCY_P99, value=600.0))
        assert "latency_p99" in result.description

    def test_description_contains_severity(self):
        service = AnomalyDetectionService(
            detector=_mock_detector(is_anomaly=True, confidence=0.7, expected_range=(10.0, 80.0))
        )
        result = service.evaluate(_make_series(value=60.0))
        assert "Severity" in result.description

    def test_build_description_static_method(self):
        desc = AnomalyDetectionService._build_description(
            MetricName.CPU_USAGE,
            value=90.0,
            expected_range=(20.0, 80.0),
            severity=AnomalySeverity.HIGH,
        )
        assert "cpu_usage" in desc
        assert "90.00" in desc
        assert "20.00" in desc
        assert "80.00" in desc
