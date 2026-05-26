"""Populate the database with realistic demo data.

Creates three patients with progressively richer history so the dashboard
has something meaningful to display:

  1. Asha Devi   - diabetic, full multi-day timeline with escalation
  2. Ravi Kumar  - elderly, multiple medications, mostly adherent
  3. Lin Wei     - newly added, only baseline data

Idempotent: re-running deletes existing demo patients before reloading.

Usage:
    python scripts/load_demo_data.py
"""
from __future__ import annotations

import io
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.event_types import CaregiverRole, EventType, Urgency
from app.models.base import utcnow
from app.models.caregiver import Caregiver, PatientCaregiver
from app.models.medication import MedicationSchedule
from app.models.patient import Patient
from app.models.reminder import Reminder, ReminderStatus
from app.services.alerts import AlertService
from app.services.care_plans import CarePlanService
from app.services.documents import DocumentService
from app.services.medications import MedicationService
from app.services.reminders import ReminderService
from app.services.summaries import SummaryService
from app.services.timeline import TimelineService
from app.services.voice_notes import VoiceNoteService
from app.schemas.care_plan import CarePlanCreate, CarePlanTaskCreate
from app.schemas.medication import MedicationScheduleCreate
from app.models.document import DocumentKind

DEMO_NAMES = {"Asha Devi (demo)", "Ravi Kumar (demo)", "Lin Wei (demo)"}


def _clear_demo(db) -> None:
    existing = db.execute(
        select(Patient).where(Patient.full_name.in_(DEMO_NAMES))
    ).scalars().all()
    for p in existing:
        db.delete(p)
    if existing:
        db.commit()


def _link_caregiver(db, *, patient: Patient, name: str, role: CaregiverRole) -> int:
    caregiver = Caregiver(full_name=name)
    db.add(caregiver)
    db.flush()
    db.add(
        PatientCaregiver(patient_id=patient.id, caregiver_id=caregiver.id, role=role)
    )
    db.commit()
    return caregiver.id


def build_asha(db) -> Patient:
    """Diabetic patient with a full multi-day timeline including escalation."""
    patient = Patient(full_name="Asha Devi (demo)", timezone="Asia/Kolkata")
    db.add(patient)
    db.commit()
    db.refresh(patient)

    son = _link_caregiver(db, patient=patient, name="Rohan (son)", role=CaregiverRole.FAMILY)
    nurse = _link_caregiver(db, patient=patient, name="Sister Maria", role=CaregiverRole.NURSE)

    cps = CarePlanService(db)
    cps.create(
        patient_id=patient.id,
        data=CarePlanCreate(
            title="Diabetes management",
            description="Daily routine for type-2 diabetes",
            created_by_caregiver_id=nurse,
            tasks=[
                CarePlanTaskCreate(title="Morning blood-sugar check", cadence="daily"),
                CarePlanTaskCreate(title="30-min walk", cadence="daily"),
                CarePlanTaskCreate(title="Weight check", cadence="weekly"),
            ],
        ),
    )

    meds = MedicationService(db)
    meds.create(
        patient_id=patient.id,
        data=MedicationScheduleCreate(
            medication_name="Metformin",
            dosage="500mg",
            times_of_day=["08:00", "20:00"],
        ),
    )
    meds.create(
        patient_id=patient.id,
        data=MedicationScheduleCreate(
            medication_name="Insulin",
            dosage="10 units",
            times_of_day=["07:30", "13:00", "19:30"],
        ),
    )

    # Backfill two days of timeline events.
    tz = ZoneInfo("Asia/Kolkata")
    today = datetime.now(tz).date()
    yesterday = today - timedelta(days=1)
    tl = TimelineService(db)

    def at(d: date, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(d, time(hour, minute)).replace(tzinfo=tz).astimezone(
            timezone.utc
        )

    # Yesterday: mostly adherent.
    tl.record(patient_id=patient.id, event_type=EventType.MEDICATION_TAKEN,
              summary="Took Metformin 500mg", occurred_at=at(yesterday, 8),
              source="patient")
    tl.record(patient_id=patient.id, event_type=EventType.MEDICATION_TAKEN,
              summary="Took Insulin 10 units", occurred_at=at(yesterday, 7, 30),
              source="patient")
    tl.record(patient_id=patient.id, event_type=EventType.CARE_PLAN_TASK_COMPLETED,
              summary="Morning walk completed", occurred_at=at(yesterday, 9),
              actor_caregiver_id=son)
    tl.record(patient_id=patient.id, event_type=EventType.MEDICATION_TAKEN,
              summary="Took Insulin 10 units", occurred_at=at(yesterday, 13))

    # Today: insulin missed twice → triggers the engine.
    tl.record(patient_id=patient.id, event_type=EventType.MEDICATION_TAKEN,
              summary="Took Metformin", occurred_at=at(today, 8))
    tl.record(
        patient_id=patient.id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        summary="Missed Insulin at 07:30",
        payload={"medication_name": "Insulin", "dose_time": "07:30"},
        occurred_at=at(today, 8),
    )
    tl.record(
        patient_id=patient.id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        summary="Missed Insulin at 13:00",
        payload={"medication_name": "Insulin", "dose_time": "13:00"},
        occurred_at=at(today, 14),
    )

    # Document upload (text → high conf).
    DocumentService(db).process(
        document_id=DocumentService(db)
        .upload(
            patient_id=patient.id,
            original_filename="rx_metformin.txt",
            mime_type="text/plain",
            data=(
                b"Dr. Sharma\n"
                b"Rx for Asha Devi\n"
                b"Metformin 500mg twice a day\n"
                b"Insulin 10 units thrice daily before meals\n"
                b"Follow up in 2 weeks\n"
            ),
            kind=DocumentKind.PRESCRIPTION,
            uploaded_by_caregiver_id=son,
        )
        .id,
    )

    # Voice note with binary bytes → forces stub fallback with missed-meds cues.
    VoiceNoteService(db).process(
        voice_note_id=VoiceNoteService(db)
        .upload(
            patient_id=patient.id,
            original_filename="evening_note.wav",
            mime_type="audio/wav",
            data=bytes(range(256)) * 6,
            recorded_by_caregiver_id=nurse,
        )
        .id,
    )

    # Today's summary.
    SummaryService(db).generate(patient_id=patient.id, target_date=today)

    return patient


def build_ravi(db) -> Patient:
    """Elderly patient with multiple medications, mostly adherent."""
    patient = Patient(full_name="Ravi Kumar (demo)", timezone="Asia/Kolkata")
    db.add(patient)
    db.commit()
    db.refresh(patient)

    daughter = _link_caregiver(db, patient=patient, name="Priya (daughter)", role=CaregiverRole.FAMILY)

    meds = MedicationService(db)
    for name, dose, times in [
        ("Atorvastatin", "20mg", ["21:00"]),
        ("Amlodipine", "5mg", ["08:00"]),
        ("Aspirin", "75mg", ["08:00"]),
    ]:
        meds.create(
            patient_id=patient.id,
            data=MedicationScheduleCreate(
                medication_name=name, dosage=dose, times_of_day=times
            ),
        )

    # Expand reminders for today and ack most of them.
    rs = ReminderService(db)
    rs.expand_for_patient(patient_id=patient.id)
    reminders = (
        db.execute(select(Reminder).where(Reminder.patient_id == patient.id))
        .scalars()
        .all()
    )
    for r in reminders[:-1]:
        r.status = ReminderStatus.SENT
        r.sent_at = utcnow() - timedelta(minutes=10)
        db.flush()
        rs.acknowledge(reminder_id=r.id, acknowledged_by_caregiver_id=daughter)

    SummaryService(db).generate(patient_id=patient.id)
    return patient


def build_lin(db) -> Patient:
    """New patient, baseline only — shows the empty-state UX."""
    patient = Patient(full_name="Lin Wei (demo)", timezone="Asia/Singapore")
    db.add(patient)
    db.commit()
    db.refresh(patient)

    _link_caregiver(db, patient=patient, name="May (caretaker)", role=CaregiverRole.CARETAKER)

    MedicationService(db).create(
        patient_id=patient.id,
        data=MedicationScheduleCreate(
            medication_name="Vitamin D",
            dosage="1000 IU",
            times_of_day=["09:00"],
        ),
    )
    return patient


def main() -> None:
    with SessionLocal() as db:
        _clear_demo(db)
    with SessionLocal() as db:
        asha = build_asha(db)
        ravi = build_ravi(db)
        lin = build_lin(db)
        print(f"created:")
        print(f"  Asha Devi (demo)  id={asha.id}  — diabetic, escalation triggered")
        print(f"  Ravi Kumar (demo) id={ravi.id}  — multi-med, mostly adherent")
        print(f"  Lin Wei (demo)    id={lin.id}  — baseline only")


if __name__ == "__main__":
    main()
