"""
LAYER 1 — DOMAIN REPOSITORIES (Interfaces/Ports)
app/domain/repositories/metric_repository.py
──────────────────────────────────────────────────────────────
LESSON: This is the DEPENDENCY INVERSION PRINCIPLE in action.

The domain defines an ABSTRACT INTERFACE for what it needs from storage.
It does NOT know HOW data is stored — in memory, Postgres, Redis, or S3.

  Domain says:  "I need something that can save and retrieve MetricSeries."
  Infrastructure says: "I'll implement that with Redis."

This means:
  - You can unit test use cases with a fake in-memory repo (no DB needed)
  - You can swap the database without changing any business logic
  - Interviewers LOVE this — it's called the "ports and adapters" pattern

ABC = Abstract Base Class — Python's way of declaring interfaces.
Any class that inherits this MUST implement all @abstractmethod methods
or Python will raise TypeError at instantiation time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.metric import MetricName, MetricPoint, MetricSeries


class IMetricRepository(ABC):
    """
    The 'I' prefix is a convention for interfaces (from Java/C# world).
    Some teams use 'Abstract' prefix or just the name — pick one and be consistent.
    """

    @abstractmethod
    async def save_point(self, point: MetricPoint) -> None:
        """Persist a single metric reading."""
        ...

    @abstractmethod
    async def get_series(
        self,
        metric: MetricName,
        since: datetime,
    ) -> MetricSeries:
        """Retrieve a full time-series for a metric since a given time."""
        ...

    @abstractmethod
    async def get_latest(self, metric: MetricName) -> MetricPoint | None:
        """Retrieve the most recent reading for a metric."""
        ...

    @abstractmethod
    async def get_all_latest(self) -> dict[MetricName, MetricPoint]:
        """Retrieve the most recent reading for every metric."""
        ...
