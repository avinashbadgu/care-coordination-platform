from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.summary import DailySummaryRead
from app.services.summaries import SummaryService

router = APIRouter(prefix="/patients/{patient_id}/summaries", tags=["summaries"])


@router.post("", response_model=DailySummaryRead, status_code=status.HTTP_201_CREATED)
def generate_summary(
    target_date: date | None = Query(default=None),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> DailySummaryRead:
    summary = SummaryService(db).generate(patient_id=patient.id, target_date=target_date)
    return DailySummaryRead.model_validate(summary)


@router.get("", response_model=list[DailySummaryRead])
def list_summaries(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[DailySummaryRead]:
    items = SummaryService(db).list_for_patient(patient.id)
    return [DailySummaryRead.model_validate(s) for s in items]
