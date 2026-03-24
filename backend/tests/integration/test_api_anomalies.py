"""Integration tests for /api/anomalies and /api/alerts endpoints."""

import pytest

from app.domain.entities.anomaly import Anomaly, AnomalySeverity
from app.domain.entities.alert import Alert
from app.domain.entities.metric import MetricName


# ── /api/anomalies ─────────────────────────────────────────────────────────────

async def test_list_anomalies_empty_by_default(client):
    response = await client.get("/api/anomalies")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_anomalies_returns_saved_anomaly(client, anomaly_repo):
    anomaly = Anomaly(
        metric=MetricName.CPU_USAGE,
        observed_value=95.0,
        expected_range=(20.0, 80.0),
        confidence=0.9,
        severity=AnomalySeverity.HIGH,
        description="Spike detected",
    )
    await anomaly_repo.save(anomaly)

    response = await client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == anomaly.id
    assert data[0]["metric"] == "cpu_usage"


async def test_list_anomalies_limit_param(client, anomaly_repo):
    for _ in range(5):
        await anomaly_repo.save(
            Anomaly(
                metric=MetricName.CPU_USAGE,
                observed_value=95.0,
                expected_range=(20.0, 80.0),
                confidence=0.9,
                severity=AnomalySeverity.HIGH,
                description="Spike",
            )
        )

    response = await client.get("/api/anomalies?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_acknowledge_nonexistent_anomaly_returns_404(client):
    response = await client.patch("/api/anomalies/does-not-exist/acknowledge")
    assert response.status_code == 404


async def test_acknowledge_existing_anomaly(client, anomaly_repo):
    anomaly = Anomaly(
        metric=MetricName.ERROR_RATE,
        observed_value=10.0,
        expected_range=(0.0, 5.0),
        confidence=0.88,
        severity=AnomalySeverity.CRITICAL,
        description="Error spike",
    )
    await anomaly_repo.save(anomaly)

    response = await client.patch(f"/api/anomalies/{anomaly.id}/acknowledge")
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True


# ── /api/alerts ────────────────────────────────────────────────────────────────

async def test_list_alerts_empty_by_default(client):
    response = await client.get("/api/alerts")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_alerts_returns_saved_alert(client, alert_repo):
    alert = Alert(
        metric=MetricName.CPU_USAGE,
        title="CPU spike",
        message="CPU usage exceeded threshold",
        severity=AnomalySeverity.HIGH,
        anomaly_id="some-anomaly-id",
    )
    await alert_repo.save(alert)

    response = await client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == alert.id


async def test_list_alerts_filter_by_status(client, alert_repo):
    alert = Alert(
        metric=MetricName.CPU_USAGE,
        title="Active alert",
        message="Test",
        severity=AnomalySeverity.LOW,
        anomaly_id="id-1",
    )
    await alert_repo.save(alert)

    response = await client.get("/api/alerts?alert_status=active")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_list_alerts_invalid_status_returns_400(client):
    response = await client.get("/api/alerts?alert_status=invalid_status")
    assert response.status_code == 400


async def test_resolve_nonexistent_alert_returns_404(client):
    response = await client.patch("/api/alerts/does-not-exist/resolve")
    assert response.status_code == 404


async def test_resolve_existing_alert(client, alert_repo):
    alert = Alert(
        metric=MetricName.LATENCY_P99,
        title="Latency spike",
        message="P99 latency exceeded 500ms",
        severity=AnomalySeverity.MEDIUM,
        anomaly_id="anomaly-123",
    )
    await alert_repo.save(alert)

    response = await client.patch(f"/api/alerts/{alert.id}/resolve")
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
