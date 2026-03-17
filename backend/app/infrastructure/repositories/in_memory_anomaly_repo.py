"""
LAYER 3 — INFRASTRUCTURE — in_memory_anomaly_repo.py
"""

from __future__ import annotations

import asyncio
from typing import Optional
from app.domain.entities.anomaly import Anomaly
from app.domain.entities.alert import Alert, AlertStatus
from app.domain.repositories.anomaly_repository import IAnomalyRepository, IAlertRepository


class InMemoryAnomalyRepository(IAnomalyRepository):
    def __init__(self) -> None:
        self._store: dict[str, Anomaly] = {}
        self._lock = asyncio.Lock()

    async def save(self, anomaly: Anomaly) -> None:
        async with self._lock:
            self._store[anomaly.id] = anomaly

    async def get_by_id(self, anomaly_id: str) -> Optional[Anomaly]:
        async with self._lock:
            return self._store.get(anomaly_id)

    async def get_recent(self, limit: int = 50) -> list[Anomaly]:
        async with self._lock:
            sorted_anomalies = sorted(
                self._store.values(),
                key=lambda a: a.detected_at,
                reverse=True,
            )
            return sorted_anomalies[:limit]

    async def acknowledge(self, anomaly_id: str) -> Anomaly:
        async with self._lock:
            anomaly = self._store.get(anomaly_id)
            if anomaly is None:
                raise ValueError(f"Anomaly {anomaly_id} not found")
            anomaly.acknowledge()  # Domain entity validates the state transition
            return anomaly


class InMemoryAlertRepository(IAlertRepository):
    def __init__(self) -> None:
        self._store: dict[str, Alert] = {}
        self._lock = asyncio.Lock()

    async def save(self, alert: Alert) -> None:
        async with self._lock:
            self._store[alert.id] = alert

    async def get_by_id(self, alert_id: str) -> Optional[Alert]:
        async with self._lock:
            return self._store.get(alert_id)

    async def get_by_status(self, status: AlertStatus) -> list[Alert]:
        async with self._lock:
            return [a for a in self._store.values() if a.status == status]

    async def update(self, alert: Alert) -> None:
        async with self._lock:
            if alert.id not in self._store:
                raise ValueError(f"Alert {alert.id} not found")
            self._store[alert.id] = alert
