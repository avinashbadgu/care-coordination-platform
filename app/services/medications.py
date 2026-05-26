from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.medication import MedicationSchedule
from app.schemas.medication import MedicationScheduleCreate
from app.services.timeline import TimelineService


class MedicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.timeline = TimelineService(db)

    def create(self, *, patient_id: int, data: MedicationScheduleCreate) -> MedicationSchedule:
        schedule = MedicationSchedule(patient_id=patient_id, **data.model_dump(exclude_none=True))
        self.db.add(schedule)
        self.db.flush()  # populate id before we record the timeline event

        self.timeline.record(
            patient_id=patient_id,
            event_type=EventType.MEDICATION_SCHEDULED,
            urgency=Urgency.LOW,
            summary=f"Scheduled {schedule.medication_name}"
            + (f" {schedule.dosage}" if schedule.dosage else ""),
            payload={
                "medication_name": schedule.medication_name,
                "dosage": schedule.dosage,
                "times_of_day": schedule.times_of_day,
            },
            related_medication_id=schedule.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def list_for_patient(self, patient_id: int) -> list[MedicationSchedule]:
        stmt = (
            select(MedicationSchedule)
            .where(MedicationSchedule.patient_id == patient_id)
            .order_by(MedicationSchedule.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
