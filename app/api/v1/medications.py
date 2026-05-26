from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.medication import MedicationScheduleCreate, MedicationScheduleRead
from app.services.medications import MedicationService

router = APIRouter(prefix="/patients/{patient_id}/medications", tags=["medications"])


@router.post("", response_model=MedicationScheduleRead, status_code=status.HTTP_201_CREATED)
def schedule_medication(
    data: MedicationScheduleCreate,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> MedicationScheduleRead:
    schedule = MedicationService(db).create(patient_id=patient.id, data=data)
    return MedicationScheduleRead.model_validate(schedule)


@router.get("", response_model=list[MedicationScheduleRead])
def list_medications(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[MedicationScheduleRead]:
    items = MedicationService(db).list_for_patient(patient.id)
    return [MedicationScheduleRead.model_validate(m) for m in items]
