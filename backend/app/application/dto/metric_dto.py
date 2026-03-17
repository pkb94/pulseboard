"""
LAYER 2 — APPLICATION DTO — app/application/dto/metric_dto.py
──────────────────────────────────────────────────────────────
LESSON: DTOs (Data Transfer Objects) are the translation layer
between the domain's internal model and the outside world.

WHY have DTOs separate from Entities?
  - Entities: internal model with business logic (frozen dataclass)
  - DTOs:     external contract serialisable to JSON (Pydantic BaseModel)
  - They can diverge: you might expose fewer fields than the entity has,
    or reshape the data for the API consumer's convenience.

Pydantic is a FRAMEWORK tool — it belongs here in application/dto/,
NOT in the domain where entities must be pure Python.

The mapping functions (from_entity) keep conversion logic in one place.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.entities.metric import MetricName, MetricPoint, MetricSeries


class MetricPointDTO(BaseModel):
    """Serialisable representation of a single data point."""
    metric: MetricName
    value: float
    timestamp: datetime

    @classmethod
    def from_entity(cls, point: MetricPoint) -> "MetricPointDTO":
        return cls(
            metric=point.metric,
            value=point.value,
            timestamp=point.timestamp,
        )


class MetricSeriesDTO(BaseModel):
    """Full time-series response sent to the frontend."""
    metric: MetricName
    label: str
    unit: str
    current: float
    change_pct: float
    threshold_upper: float | None = None
    threshold_lower: float | None = None
    data: list[MetricPointDTO] = Field(default_factory=list)

    # Map readable labels and units from domain enum values
    _LABELS: dict[MetricName, str] = {
        MetricName.CPU_USAGE: "CPU Usage",
        MetricName.MEMORY_USAGE: "Memory Usage",
        MetricName.REQUEST_RATE: "Request Rate",
        MetricName.ERROR_RATE: "Error Rate",
        MetricName.LATENCY_P99: "Latency (P99)",
        MetricName.THROUGHPUT: "Throughput",
        MetricName.REVENUE_PER_MIN: "Revenue / Min",
        MetricName.ACTIVE_USERS: "Active Users",
    }

    _UNITS: dict[MetricName, str] = {
        MetricName.CPU_USAGE: "%",
        MetricName.MEMORY_USAGE: "%",
        MetricName.REQUEST_RATE: "req/s",
        MetricName.ERROR_RATE: "%",
        MetricName.LATENCY_P99: "ms",
        MetricName.THROUGHPUT: "req/s",
        MetricName.REVENUE_PER_MIN: "USD/min",
        MetricName.ACTIVE_USERS: "users",
    }

    @classmethod
    def from_entity(cls, series: MetricSeries) -> "MetricSeriesDTO":
        return cls(
            metric=series.metric,
            label=cls._LABELS.get(series.metric, series.metric.value),
            unit=cls._UNITS.get(series.metric, ""),
            current=series.current_value,
            change_pct=series.change_pct(),
            threshold_upper=series.threshold_upper,
            threshold_lower=series.threshold_lower,
            data=[MetricPointDTO.from_entity(p) for p in series.points[-60:]],
        )


class MetricsSnapshotDTO(BaseModel):
    """All current metric values in one response (for dashboard load)."""
    metrics: list[MetricSeriesDTO]
    snapshot_at: datetime = Field(default_factory=datetime.utcnow)
