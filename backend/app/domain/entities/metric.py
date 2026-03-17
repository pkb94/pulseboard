"""
LAYER 1 — DOMAIN ENTITIES — app/domain/entities/metric.py
──────────────────────────────────────────────────────────
LESSON: Entities are the heart of Clean Architecture.
They represent REAL-WORLD CONCEPTS with business rules baked in.

Rules for this file:
  ✅ Pure Python — no FastAPI, no Pydantic, no SQLAlchemy
  ✅ Business logic lives HERE (e.g., is_in_alert_range)
  ❌ Never import from application/, infrastructure/, or presentation/

WHY dataclasses? They give us __init__, __repr__, __eq__ for free
without depending on any web framework. Pydantic is a framework tool
— it belongs in the DTO layer (application/dto/).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricName(str, Enum):
    """
    Using an Enum for metric names is a domain decision.
    It prevents typos, enables IDE autocomplete, and makes
    the set of valid metrics explicit and discoverable.
    """
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"
    ERROR_RATE = "error_rate"
    LATENCY_P99 = "latency_p99"
    THROUGHPUT = "throughput"
    REVENUE_PER_MIN = "revenue_per_min"
    ACTIVE_USERS = "active_users"


@dataclass(frozen=True)
class MetricPoint:
    """
    A single reading of a metric at a point in time.
    frozen=True makes it immutable — a metric reading is a historical fact
    that should never be mutated after creation.
    """
    metric: MetricName
    value: float
    timestamp: datetime

    def __post_init__(self) -> None:
        """
        __post_init__ is where dataclass validation lives.
        This replaces Pydantic validators at the domain level.
        """
        if self.value < 0 and self.metric not in (
            MetricName.REVENUE_PER_MIN,  # revenue could theoretically go negative
        ):
            raise ValueError(f"Metric value cannot be negative: {self.metric}={self.value}")


@dataclass
class MetricSeries:
    """
    A time-series collection of readings for one metric.
    Aggregates MetricPoints and provides domain-level computations.
    """
    metric: MetricName
    points: list[MetricPoint] = field(default_factory=list)
    threshold_upper: Optional[float] = None
    threshold_lower: Optional[float] = None

    @property
    def latest(self) -> Optional[MetricPoint]:
        """Most recent reading — O(1) if list is sorted, fine for our use case."""
        return self.points[-1] if self.points else None

    @property
    def current_value(self) -> float:
        return self.latest.value if self.latest else 0.0

    def change_pct(self, window: int = 5) -> float:
        """
        Percentage change vs. `window` readings ago.
        Pure business logic — no framework involved.
        """
        if len(self.points) < window + 1:
            return 0.0
        old = self.points[-(window + 1)].value
        new = self.points[-1].value
        if old == 0:
            return 0.0
        return round(((new - old) / old) * 100, 2)

    def is_breaching_threshold(self) -> bool:
        """Domain rule: is the current value outside configured thresholds?"""
        val = self.current_value
        if self.threshold_upper is not None and val > self.threshold_upper:
            return True
        if self.threshold_lower is not None and val < self.threshold_lower:
            return True
        return False

    def add_point(self, point: MetricPoint) -> None:
        """Keep only last 300 points (5 min at 1s interval) in memory."""
        self.points.append(point)
        if len(self.points) > 300:
            self.points = self.points[-300:]
