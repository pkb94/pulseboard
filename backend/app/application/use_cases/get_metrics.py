"""
LAYER 2 — USE CASE — app/application/use_cases/get_metrics.py
──────────────────────────────────────────────────────────────
LESSON: Use Cases are the APPLICATION'S business logic.

They answer the question: "What does the system DO?"
  - GetMetricsUseCase: "Fetch all current metrics for the dashboard"
  - DetectAnomaliesUseCase: "Process new data, check for anomalies"
  - ResolveAlertUseCase: "Mark an alert as resolved"

Each use case is a single, focused class with ONE public method.
This is the Single Responsibility Principle applied at the use-case level.

Use cases:
  ✅ Receive repository interfaces (injected in __init__)
  ✅ Orchestrate calls between repositories and domain services
  ✅ Return DTOs (not raw entities) to keep the interface stable
  ❌ Never contain HTTP-specific logic (no Request/Response objects)
  ❌ Never contain SQL, ORM calls, or ML library code
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.application.dto.metric_dto import MetricSeriesDTO, MetricsSnapshotDTO
from app.domain.entities.metric import MetricName
from app.domain.repositories.metric_repository import IMetricRepository


class GetMetricsUseCase:
    """
    Retrieves the current metrics snapshot for the dashboard.
    Injected repository means this is trivially unit-testable.
    """

    def __init__(self, metric_repo: IMetricRepository) -> None:
        # Constructor injection — the use case declares what it NEEDS
        # without caring about HOW it's implemented.
        self._repo = metric_repo

    async def execute(self, window_minutes: int = 60) -> MetricsSnapshotDTO:
        """
        Single entry point. Returns all metric series for the given window.
        'execute()' is the conventional name for use case entry points.
        """
        since = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Fetch all metric series concurrently
        import asyncio
        series_list = await asyncio.gather(*[
            self._repo.get_series(metric, since)
            for metric in MetricName
        ])

        return MetricsSnapshotDTO(
            metrics=[MetricSeriesDTO.from_entity(s) for s in series_list]
        )


class GetSingleMetricUseCase:
    """Retrieves history for a single metric — used for drill-down views."""

    def __init__(self, metric_repo: IMetricRepository) -> None:
        self._repo = metric_repo

    async def execute(self, metric: MetricName, window_minutes: int = 60) -> MetricSeriesDTO:
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        series = await self._repo.get_series(metric, since)
        return MetricSeriesDTO.from_entity(series)
