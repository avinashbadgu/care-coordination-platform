from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.reminder import ReminderAck, ReminderRead
from app.services.reminders import ReminderService

router = APIRouter(tags=["reminders"])


@router.post(
    "/patients/{patient_id}/reminders/expand",
    response_model=list[ReminderRead],
    status_code=status.HTTP_200_OK,
)
def expand_reminders(
    target_date: date | None = Query(default=None),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[ReminderRead]:
    created = ReminderService(db).expand_for_patient(
        patient_id=patient.id, target_date=target_date
    )
    return [ReminderRead.model_validate(r) for r in created]


@router.get("/patients/{patient_id}/reminders", response_model=list[ReminderRead])
def list_reminders(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[ReminderRead]:
    items = ReminderService(db).list_for_patient(patient.id)
    return [ReminderRead.model_validate(r) for r in items]


@router.post("/reminders/dispatch", response_model=dict[str, int])
def dispatch_due(db: Session = Depends(get_db)) -> dict[str, int]:
    sent = ReminderService(db).dispatch_due()
    return {"sent": sent}


@router.post("/reminders/detect-misses", response_model=dict[str, int])
def detect_misses(db: Session = Depends(get_db)) -> dict[str, int]:
    missed = ReminderService(db).detect_misses()
    return {"missed": missed}


@router.post("/reminders/{reminder_id}/ack", response_model=ReminderRead)
def ack_reminder(
    reminder_id: int,
    data: ReminderAck = Body(default_factory=ReminderAck),
    db: Session = Depends(get_db),
) -> ReminderRead:
    reminder = ReminderService(db).acknowledge(
        reminder_id=reminder_id,
        acknowledged_by_caregiver_id=data.acknowledged_by_caregiver_id,
        notes=data.notes,
    )
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="reminder not found")
    return ReminderRead.model_validate(reminder)
