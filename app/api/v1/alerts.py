from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.alert import AlertCreate, AlertRead, AlertResolve
from app.services.alerts import AlertService

router = APIRouter(tags=["alerts"])


@router.post(
    "/patients/{patient_id}/alerts",
    response_model=AlertRead,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(
    data: AlertCreate,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> AlertRead:
    alert = AlertService(db).raise_alert(
        patient_id=patient.id,
        urgency=data.urgency,
        title=data.title,
        detail=data.detail,
    )
    return AlertRead.model_validate(alert)


@router.get("/patients/{patient_id}/alerts", response_model=list[AlertRead])
def list_alerts(
    only_open: bool = Query(False),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[AlertRead]:
    items = AlertService(db).list_for_patient(patient_id=patient.id, only_open=only_open)
    return [AlertRead.model_validate(a) for a in items]


@router.post("/alerts/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(
    alert_id: int,
    data: AlertResolve = Body(default_factory=AlertResolve),
    db: Session = Depends(get_db),
) -> AlertRead:
    alert = AlertService(db).resolve_alert(
        alert_id=alert_id,
        resolved_by_caregiver_id=data.resolved_by_caregiver_id,
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    return AlertRead.model_validate(alert)
