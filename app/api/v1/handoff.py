from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.handoff import HandoffSummary
from app.services.handoff import HandoffService

router = APIRouter(prefix="/patients/{patient_id}/handoff", tags=["handoff"])


@router.get("", response_model=HandoffSummary)
def get_handoff(
    hours: int = Query(12, ge=1, le=72),
    window_start: datetime | None = Query(default=None),
    window_end: datetime | None = Query(default=None),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> HandoffSummary:
    result = HandoffService(db).generate(
        patient_id=patient.id,
        window_start=window_start,
        window_end=window_end,
        hours=hours,
    )
    return HandoffSummary(**result)
