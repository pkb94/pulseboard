"""Integration tests for /api/health endpoints."""

import pytest


async def test_health_check_returns_200(client):
    response = await client.get("/api/health")
    assert response.status_code == 200


async def test_health_check_status_is_healthy(client):
    response = await client.get("/api/health")
    assert response.json()["status"] == "healthy"


async def test_health_check_has_timestamp(client):
    response = await client.get("/api/health")
    data = response.json()
    assert "timestamp" in data
    assert data["timestamp"]  # non-empty


async def test_health_check_has_version(client):
    response = await client.get("/api/health")
    assert response.json()["version"] == "1.0.0"


async def test_system_health_returns_200(client):
    response = await client.get("/api/health/system")
    assert response.status_code == 200


async def test_system_health_status_operational(client):
    response = await client.get("/api/health/system")
    assert response.json()["status"] == "operational"


async def test_system_health_has_services_list(client):
    response = await client.get("/api/health/system")
    data = response.json()
    assert "services" in data
    assert len(data["services"]) > 0
