from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.caregiver import Caregiver, PatientCaregiver
from app.schemas.caregiver import CaregiverCreate, PatientCaregiverLinkCreate


class CaregiverService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: CaregiverCreate) -> Caregiver:
        caregiver = Caregiver(**data.model_dump(exclude_none=True))
        self.db.add(caregiver)
        self.db.commit()
        self.db.refresh(caregiver)
        return caregiver

    def get(self, caregiver_id: int) -> Caregiver | None:
        return self.db.get(Caregiver, caregiver_id)

    def list(self, *, limit: int = 100, offset: int = 0) -> tuple[list[Caregiver], int]:
        stmt = select(Caregiver).order_by(Caregiver.id.desc())
        total = len(self.db.execute(select(Caregiver.id)).all())
        items = list(self.db.execute(stmt.limit(limit).offset(offset)).scalars().all())
        return items, total

    def link_to_patient(
        self, *, patient_id: int, data: PatientCaregiverLinkCreate
    ) -> PatientCaregiver:
        link = PatientCaregiver(
            patient_id=patient_id,
            caregiver_id=data.caregiver_id,
            role=data.role,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_links_for_patient(self, patient_id: int) -> list[PatientCaregiver]:
        stmt = select(PatientCaregiver).where(PatientCaregiver.patient_id == patient_id)
        return list(self.db.execute(stmt).scalars().all())
