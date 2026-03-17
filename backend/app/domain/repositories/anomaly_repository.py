"""
LAYER 1 — DOMAIN REPOSITORIES (Interfaces)
app/domain/repositories/anomaly_repository.py + alert_repository.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.anomaly import Anomaly
from app.domain.entities.alert import Alert, AlertStatus


class IAnomalyRepository(ABC):

    @abstractmethod
    async def save(self, anomaly: Anomaly) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, anomaly_id: str) -> Anomaly | None:
        ...

    @abstractmethod
    async def get_recent(self, limit: int = 50) -> list[Anomaly]:
        ...

    @abstractmethod
    async def acknowledge(self, anomaly_id: str) -> Anomaly:
        ...


class IAlertRepository(ABC):

    @abstractmethod
    async def save(self, alert: Alert) -> None:
        ...

    @abstractmethod
    async def get_by_id(self, alert_id: str) -> Alert | None:
        ...

    @abstractmethod
    async def get_by_status(self, status: AlertStatus) -> list[Alert]:
        ...

    @abstractmethod
    async def update(self, alert: Alert) -> None:
        ...
