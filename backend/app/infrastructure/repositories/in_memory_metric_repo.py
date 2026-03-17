"""
LAYER 3 — INFRASTRUCTURE — app/infrastructure/repositories/in_memory_metric_repo.py
──────────────────────────────────────────────────────────────────────────────────────
LESSON: This is the CONCRETE IMPLEMENTATION of the domain interface.

It inherits IMetricRepository and provides real business logic using
an in-memory data structure. In production you'd have a RedisMetricRepository
or TimescaleDBMetricRepository — the rest of the app wouldn't change at all.

Key interview point: "How would you scale this to production?"
Answer: "Replace this class with a TimescaleDB or InfluxDB adapter.
        The use cases, domain service, and API routes stay identical."
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Optional

from app.domain.entities.metric import MetricName, MetricPoint, MetricSeries
from app.domain.repositories.metric_repository import IMetricRepository

# Default thresholds — would come from a config DB in production
_DEFAULT_THRESHOLDS: dict[MetricName, dict[str, float]] = {
    MetricName.CPU_USAGE:       {"upper": 85.0},
    MetricName.MEMORY_USAGE:    {"upper": 90.0},
    MetricName.ERROR_RATE:      {"upper": 5.0},
    MetricName.LATENCY_P99:     {"upper": 500.0},
    MetricName.REQUEST_RATE:    {"lower": 10.0},
}


class InMemoryMetricRepository(IMetricRepository):
    """
    Thread-safe in-memory metric store using asyncio.Lock.
    Perfect for demos, local testing, and single-instance services.
    """

    def __init__(self) -> None:
        # dict[MetricName → list[MetricPoint]] (chronological order)
        self._store: dict[MetricName, list[MetricPoint]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def save_point(self, point: MetricPoint) -> None:
        async with self._lock:
            self._store[point.metric].append(point)
            # Keep a rolling window of 600 points (10 min at 1s interval)
            if len(self._store[point.metric]) > 600:
                self._store[point.metric] = self._store[point.metric][-600:]

    async def get_series(self, metric: MetricName, since: datetime) -> MetricSeries:
        async with self._lock:
            points = [
                p for p in self._store.get(metric, [])
                if p.timestamp >= since
            ]

        thresholds = _DEFAULT_THRESHOLDS.get(metric, {})
        series = MetricSeries(
            metric=metric,
            points=points,
            threshold_upper=thresholds.get("upper"),
            threshold_lower=thresholds.get("lower"),
        )
        return series

    async def get_latest(self, metric: MetricName) -> Optional[MetricPoint]:
        async with self._lock:
            pts = self._store.get(metric, [])
            return pts[-1] if pts else None

    async def get_all_latest(self) -> dict[MetricName, MetricPoint]:
        async with self._lock:
            return {
                metric: pts[-1]
                for metric, pts in self._store.items()
                if pts
            }
