from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.common import Page
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.patients import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    patient = PatientService(db).create(data)
    return PatientRead.model_validate(patient)


@router.get("", response_model=Page[PatientRead])
def list_patients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[PatientRead]:
    items, total = PatientService(db).list(limit=limit, offset=offset)
    return Page[PatientRead](
        items=[PatientRead.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient: Patient = Depends(get_existing_patient)) -> PatientRead:
    return PatientRead.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = PatientService(db).update(patient_id, data)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient not found")
    return PatientRead.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db)) -> None:
    ok = PatientService(db).delete(patient_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient not found")
