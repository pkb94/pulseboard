"""
LAYER 4 — PRESENTATION — app/presentation/api/routes/anomalies.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.application.dto.anomaly_dto import AlertDTO, AnomalyDTO
from app.application.use_cases.detect_anomalies import (
    AcknowledgeAnomalyUseCase,
    ResolveAlertUseCase,
)
from app.core.dependencies import (
    get_acknowledge_anomaly_use_case,
    get_resolve_alert_use_case,
    get_anomaly_repo,
    get_alert_repo,
)
from app.domain.entities.alert import AlertStatus
from app.domain.repositories.anomaly_repository import IAnomalyRepository, IAlertRepository

router = APIRouter(tags=["anomalies"])


@router.get("/api/anomalies", response_model=list[AnomalyDTO])
async def list_anomalies(
    limit: int = 50,
    repo: IAnomalyRepository = Depends(get_anomaly_repo),
) -> list[AnomalyDTO]:
    anomalies = await repo.get_recent(limit=limit)
    return [AnomalyDTO.from_entity(a) for a in anomalies]


@router.patch("/api/anomalies/{anomaly_id}/acknowledge", response_model=AnomalyDTO)
async def acknowledge_anomaly(
    anomaly_id: str,
    use_case: AcknowledgeAnomalyUseCase = Depends(get_acknowledge_anomaly_use_case),
) -> AnomalyDTO:
    try:
        return await use_case.execute(anomaly_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/api/alerts", response_model=list[AlertDTO])
async def list_alerts(
    alert_status: str | None = None,
    repo: IAlertRepository = Depends(get_alert_repo),
) -> list[AlertDTO]:
    if alert_status:
        try:
            parsed = AlertStatus(alert_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {alert_status}",
            )
        alerts = await repo.get_by_status(parsed)
    else:
        # Return all alerts (active first)
        active = await repo.get_by_status(AlertStatus.ACTIVE)
        acked = await repo.get_by_status(AlertStatus.ACKNOWLEDGED)
        resolved = await repo.get_by_status(AlertStatus.RESOLVED)
        alerts = active + acked + resolved

    return [AlertDTO.from_entity(a) for a in alerts]


@router.patch("/api/alerts/{alert_id}/resolve", response_model=AlertDTO)
async def resolve_alert(
    alert_id: str,
    use_case: ResolveAlertUseCase = Depends(get_resolve_alert_use_case),
) -> AlertDTO:
    try:
        return await use_case.execute(alert_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
