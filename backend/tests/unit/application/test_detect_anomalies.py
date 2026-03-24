"""Unit tests for DetectAnomaliesUseCase, AcknowledgeAnomalyUseCase, ResolveAlertUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.application.use_cases.detect_anomalies import (
    AcknowledgeAnomalyUseCase,
    DetectAnomaliesUseCase,
    ResolveAlertUseCase,
)
from app.domain.entities.alert import Alert, AlertStatus
from app.domain.entities.anomaly import Anomaly, AnomalySeverity
from app.domain.entities.metric import MetricName, MetricSeries


def _make_anomaly() -> Anomaly:
    return Anomaly(
        metric=MetricName.CPU_USAGE,
        observed_value=95.0,
        expected_range=(20.0, 80.0),
        confidence=0.9,
        severity=AnomalySeverity.HIGH,
        description="Test anomaly",
    )


def _make_alert() -> Alert:
    return Alert(
        metric=MetricName.CPU_USAGE,
        title="Test alert",
        message="Test message",
        severity=AnomalySeverity.HIGH,
        anomaly_id="some-anomaly-id",
    )


def _build_detect_use_case(detection_service):
    metric_repo = AsyncMock()
    anomaly_repo = AsyncMock()
    alert_repo = AsyncMock()
    broadcast = AsyncMock()

    metric_repo.save_point = AsyncMock()
    metric_repo.get_series = AsyncMock(
        return_value=MetricSeries(metric=MetricName.CPU_USAGE, points=[])
    )
    anomaly_repo.save = AsyncMock()
    alert_repo.save = AsyncMock()

    use_case = DetectAnomaliesUseCase(
        metric_repo=metric_repo,
        anomaly_repo=anomaly_repo,
        alert_repo=alert_repo,
        detection_service=detection_service,
        broadcast_fn=broadcast,
    )
    return use_case, metric_repo, anomaly_repo, alert_repo, broadcast


class TestDetectAnomaliesUseCase:
    async def test_saves_metric_point_regardless_of_anomaly(self):
        svc = MagicMock()
        svc.evaluate.return_value = None
        use_case, metric_repo, _, _, _ = _build_detect_use_case(svc)

        await use_case.execute(MetricName.CPU_USAGE, 50.0)

        metric_repo.save_point.assert_called_once()

    async def test_returns_none_when_no_anomaly(self):
        svc = MagicMock()
        svc.evaluate.return_value = None
        use_case, _, _, _, broadcast = _build_detect_use_case(svc)

        result = await use_case.execute(MetricName.CPU_USAGE, 50.0)

        assert result is None
        broadcast.assert_not_called()

    async def test_returns_anomaly_dto_on_detection(self):
        anomaly = _make_anomaly()
        svc = MagicMock()
        svc.evaluate.return_value = anomaly
        use_case, _, _, _, _ = _build_detect_use_case(svc)

        result = await use_case.execute(MetricName.CPU_USAGE, 95.0)

        assert result is not None
        assert result.metric == MetricName.CPU_USAGE

    async def test_saves_anomaly_when_detected(self):
        anomaly = _make_anomaly()
        svc = MagicMock()
        svc.evaluate.return_value = anomaly
        use_case, _, anomaly_repo, _, _ = _build_detect_use_case(svc)

        await use_case.execute(MetricName.CPU_USAGE, 95.0)

        anomaly_repo.save.assert_called_once_with(anomaly)

    async def test_saves_alert_when_anomaly_detected(self):
        svc = MagicMock()
        svc.evaluate.return_value = _make_anomaly()
        use_case, _, _, alert_repo, _ = _build_detect_use_case(svc)

        await use_case.execute(MetricName.CPU_USAGE, 95.0)

        alert_repo.save.assert_called_once()

    async def test_broadcasts_on_anomaly(self):
        svc = MagicMock()
        svc.evaluate.return_value = _make_anomaly()
        use_case, _, _, _, broadcast = _build_detect_use_case(svc)

        await use_case.execute(MetricName.CPU_USAGE, 95.0)

        broadcast.assert_called_once()

    async def test_broadcast_payload_has_correct_type(self):
        svc = MagicMock()
        svc.evaluate.return_value = _make_anomaly()
        use_case, _, _, _, broadcast = _build_detect_use_case(svc)

        await use_case.execute(MetricName.CPU_USAGE, 95.0)

        payload = broadcast.call_args[0][0]
        assert payload["type"] == "anomaly_detected"
        assert "payload" in payload
        assert "alert" in payload


class TestAcknowledgeAnomalyUseCase:
    async def test_returns_acknowledged_anomaly_dto(self):
        anomaly = _make_anomaly()
        anomaly.acknowledge()

        repo = AsyncMock()
        repo.acknowledge = AsyncMock(return_value=anomaly)

        use_case = AcknowledgeAnomalyUseCase(anomaly_repo=repo)
        result = await use_case.execute(anomaly.id)

        assert result.acknowledged is True

    async def test_calls_repo_with_correct_id(self):
        anomaly = _make_anomaly()
        anomaly.acknowledge()

        repo = AsyncMock()
        repo.acknowledge = AsyncMock(return_value=anomaly)

        use_case = AcknowledgeAnomalyUseCase(anomaly_repo=repo)
        await use_case.execute("specific-anomaly-id")

        repo.acknowledge.assert_called_once_with("specific-anomaly-id")

    async def test_propagates_value_error_from_repo(self):
        repo = AsyncMock()
        repo.acknowledge = AsyncMock(side_effect=ValueError("not found"))

        use_case = AcknowledgeAnomalyUseCase(anomaly_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await use_case.execute("nonexistent-id")


class TestResolveAlertUseCase:
    async def test_resolves_active_alert(self):
        alert = _make_alert()
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=alert)
        repo.update = AsyncMock()

        use_case = ResolveAlertUseCase(alert_repo=repo)
        result = await use_case.execute(alert.id)

        assert result.status == AlertStatus.RESOLVED

    async def test_updates_alert_in_repo(self):
        alert = _make_alert()
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=alert)
        repo.update = AsyncMock()

        use_case = ResolveAlertUseCase(alert_repo=repo)
        await use_case.execute(alert.id)

        repo.update.assert_called_once()

    async def test_raises_when_alert_not_found(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)

        use_case = ResolveAlertUseCase(alert_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await use_case.execute("nonexistent-id")
