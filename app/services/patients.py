from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: PatientCreate) -> Patient:
        patient = Patient(**data.model_dump(exclude_none=True))
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def get(self, patient_id: int) -> Patient | None:
        return self.db.get(Patient, patient_id)

    def list(self, *, limit: int = 100, offset: int = 0) -> tuple[list[Patient], int]:
        stmt = select(Patient).order_by(Patient.id.desc())
        total = len(self.db.execute(select(Patient.id)).all())
        items = list(self.db.execute(stmt.limit(limit).offset(offset)).scalars().all())
        return items, total

    def update(self, patient_id: int, data: PatientUpdate) -> Patient | None:
        patient = self.get(patient_id)
        if patient is None:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(patient, k, v)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def delete(self, patient_id: int) -> bool:
        patient = self.get(patient_id)
        if patient is None:
            return False
        self.db.delete(patient)
        self.db.commit()
        return True
