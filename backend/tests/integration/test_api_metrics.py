"""Integration tests for /api/metrics endpoints."""

import pytest

from app.domain.entities.metric import MetricName


async def test_get_all_metrics_returns_200(client):
    response = await client.get("/api/metrics")
    assert response.status_code == 200


async def test_get_all_metrics_returns_correct_count(client):
    response = await client.get("/api/metrics")
    data = response.json()
    assert len(data["metrics"]) == len(MetricName)


async def test_get_all_metrics_has_snapshot_at(client):
    response = await client.get("/api/metrics")
    assert "snapshot_at" in response.json()


async def test_get_all_metrics_each_item_has_required_fields(client):
    response = await client.get("/api/metrics")
    for item in response.json()["metrics"]:
        assert "metric" in item
        assert "label" in item
        assert "unit" in item
        assert "current" in item
        assert "change_pct" in item


async def test_get_all_metrics_respects_window_param(client):
    response = await client.get("/api/metrics?window_minutes=30")
    assert response.status_code == 200


async def test_get_single_metric_cpu_usage(client):
    response = await client.get("/api/metrics/cpu_usage")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "cpu_usage"
    assert data["label"] == "CPU Usage"
    assert data["unit"] == "%"


async def test_get_single_metric_error_rate(client):
    response = await client.get("/api/metrics/error_rate")
    assert response.status_code == 200
    assert response.json()["metric"] == "error_rate"


async def test_get_single_metric_with_window(client):
    response = await client.get("/api/metrics/latency_p99?window_minutes=15")
    assert response.status_code == 200


async def test_get_single_metric_invalid_name_returns_400(client):
    response = await client.get("/api/metrics/totally_fake_metric")
    assert response.status_code == 400


async def test_get_single_metric_invalid_name_detail_mentions_metric(client):
    response = await client.get("/api/metrics/totally_fake_metric")
    assert "Unknown metric" in response.json()["detail"]
