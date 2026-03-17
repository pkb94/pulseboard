"""
LAYER 4 — PRESENTATION — app/presentation/api/routes/metrics.py
────────────────────────────────────────────────────────────────
LESSON: FastAPI routers are the outermost layer.
They ONLY do 3 things:
  1. Parse the HTTP request (path params, query params, body)
  2. Call a use case
  3. Return the DTO as JSON

Business logic does NOT live here. If you find yourself writing
if/else business conditions in a router, move it to a use case.

FastAPI's dependency injection system (Depends) is how we wire
the use case with its concrete repository implementations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.application.dto.metric_dto import MetricSeriesDTO, MetricsSnapshotDTO
from app.application.use_cases.get_metrics import GetMetricsUseCase, GetSingleMetricUseCase
from app.domain.entities.metric import MetricName
from app.core.dependencies import get_metrics_use_case, get_single_metric_use_case

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=MetricsSnapshotDTO)
async def get_all_metrics(
    window_minutes: int = 60,
    use_case: GetMetricsUseCase = Depends(get_metrics_use_case),
) -> MetricsSnapshotDTO:
    """
    Returns the current snapshot of ALL metrics.
    Used by the dashboard on initial load.
    """
    return await use_case.execute(window_minutes=window_minutes)


@router.get("/{metric_name}", response_model=MetricSeriesDTO)
async def get_metric(
    metric_name: str,
    window_minutes: int = 60,
    use_case: GetSingleMetricUseCase = Depends(get_single_metric_use_case),
) -> MetricSeriesDTO:
    """
    Returns the time-series for a single metric.
    Used when a user clicks into a specific chart for detail.
    """
    try:
        metric = MetricName(metric_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown metric: {metric_name}. Valid metrics: {[m.value for m in MetricName]}",
        )
    return await use_case.execute(metric=metric, window_minutes=window_minutes)
