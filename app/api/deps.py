from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db as _get_db
from app.models.patient import Patient


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_existing_patient(patient_id: int, db: Session = Depends(get_db)) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="patient not found")
    return patient
