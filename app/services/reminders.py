from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.base import utcnow
from app.models.medication import MedicationSchedule
from app.models.reminder import Reminder, ReminderStatus
from app.services.timeline import TimelineService

log = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.timeline = TimelineService(db)

    # ----- expansion ----------------------------------------------------

    def expand_for_patient(
        self, *, patient_id: int, target_date: date | None = None
    ) -> list[Reminder]:
        """Idempotently create Reminder rows for the given calendar day."""
        from app.models.patient import Patient

        patient = self.db.get(Patient, patient_id)
        if patient is None:
            return []
        tz = ZoneInfo(patient.timezone)
        target_date = target_date or datetime.now(tz).date()

        schedules = list(
            self.db.execute(
                select(MedicationSchedule).where(
                    MedicationSchedule.patient_id == patient_id,
                    MedicationSchedule.active.is_(True),
                )
            ).scalars()
        )

        created: list[Reminder] = []
        for schedule in schedules:
            if schedule.starts_on and target_date < schedule.starts_on:
                continue
            if schedule.ends_on and target_date > schedule.ends_on:
                continue
            for hhmm in schedule.times_of_day:
                hh, mm = (int(x) for x in hhmm.split(":"))
                local_dt = datetime.combine(target_date, time(hh, mm)).replace(tzinfo=tz)
                fire_at = local_dt.astimezone(timezone.utc)

                exists = self.db.execute(
                    select(Reminder.id).where(
                        Reminder.medication_schedule_id == schedule.id,
                        Reminder.scheduled_for == fire_at,
                    )
                ).first()
                if exists:
                    continue

                reminder = Reminder(
                    patient_id=patient_id,
                    medication_schedule_id=schedule.id,
                    scheduled_for=fire_at,
                    status=ReminderStatus.PENDING,
                )
                self.db.add(reminder)
                created.append(reminder)
        self.db.commit()
        return created

    # ----- dispatch -----------------------------------------------------

    def dispatch_due(self, *, now: datetime | None = None) -> int:
        """Send all reminders whose scheduled_for has arrived."""
        from app.services.notifications import NotificationService

        now = now or utcnow()
        stmt = select(Reminder).where(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.scheduled_for <= now,
        )
        due = list(self.db.execute(stmt).scalars())

        notifications = NotificationService()
        sent = 0
        for reminder in due:
            schedule = (
                self.db.get(MedicationSchedule, reminder.medication_schedule_id)
                if reminder.medication_schedule_id
                else None
            )
            label = schedule.medication_name if schedule else "Medication"
            success, channel, attempts = notifications.send_reminder(
                patient_id=reminder.patient_id,
                title=f"Time for {label}",
                body=(f"Please take {label}"
                      + (f" {schedule.dosage}" if schedule and schedule.dosage else "")),
            )
            reminder.retries = attempts - 1
            reminder.channel = channel
            if success:
                reminder.status = ReminderStatus.SENT
                reminder.sent_at = utcnow()
                self.timeline.record(
                    patient_id=reminder.patient_id,
                    event_type=EventType.REMINDER_SENT,
                    summary=f"Reminder sent: {label}",
                    payload={
                        "reminder_id": reminder.id,
                        "channel": channel,
                        "attempts": attempts,
                    },
                    related_reminder_id=reminder.id,
                    related_medication_id=reminder.medication_schedule_id,
                    commit=False,
                )
                sent += 1
            else:
                reminder.status = ReminderStatus.FAILED
                self.timeline.record(
                    patient_id=reminder.patient_id,
                    event_type=EventType.REMINDER_FAILED,
                    urgency=Urgency.MEDIUM,
                    summary=f"Reminder failed: {label}",
                    payload={"reminder_id": reminder.id, "attempts": attempts},
                    related_reminder_id=reminder.id,
                    commit=False,
                )
        self.db.commit()
        return sent

    # ----- ack / miss ---------------------------------------------------

    def acknowledge(
        self,
        *,
        reminder_id: int,
        acknowledged_by_caregiver_id: int | None = None,
        notes: str | None = None,
    ) -> Reminder | None:
        reminder = self.db.get(Reminder, reminder_id)
        if reminder is None:
            return None
        if reminder.status == ReminderStatus.ACKNOWLEDGED:
            return reminder

        reminder.status = ReminderStatus.ACKNOWLEDGED
        reminder.acknowledged_at = utcnow()
        self.db.flush()

        schedule = (
            self.db.get(MedicationSchedule, reminder.medication_schedule_id)
            if reminder.medication_schedule_id
            else None
        )

        self.timeline.record(
            patient_id=reminder.patient_id,
            event_type=EventType.REMINDER_ACKNOWLEDGED,
            summary=(
                f"Reminder acknowledged: {schedule.medication_name}"
                if schedule
                else "Reminder acknowledged"
            ),
            payload={"reminder_id": reminder.id, "notes": notes},
            actor_caregiver_id=acknowledged_by_caregiver_id,
            related_reminder_id=reminder.id,
            commit=False,
        )
        if schedule:
            self.timeline.record(
                patient_id=reminder.patient_id,
                event_type=EventType.MEDICATION_TAKEN,
                summary=f"Took {schedule.medication_name}",
                payload={
                    "reminder_id": reminder.id,
                    "medication_name": schedule.medication_name,
                    "dosage": schedule.dosage,
                },
                actor_caregiver_id=acknowledged_by_caregiver_id,
                related_reminder_id=reminder.id,
                related_medication_id=schedule.id,
                commit=False,
            )
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def detect_misses(self, *, grace: timedelta = timedelta(hours=1)) -> int:
        """Mark un-acknowledged reminders past their grace window as missed."""
        cutoff = utcnow() - grace
        stmt = select(Reminder).where(
            Reminder.status.in_([ReminderStatus.SENT, ReminderStatus.PENDING]),
            Reminder.scheduled_for <= cutoff,
        )
        candidates = list(self.db.execute(stmt).scalars())
        missed = 0
        for reminder in candidates:
            reminder.status = ReminderStatus.MISSED
            self.db.flush()
            schedule = (
                self.db.get(MedicationSchedule, reminder.medication_schedule_id)
                if reminder.medication_schedule_id
                else None
            )
            self.timeline.record(
                patient_id=reminder.patient_id,
                event_type=EventType.MEDICATION_MISSED,
                urgency=Urgency.MEDIUM,
                summary=(
                    f"Missed dose: {schedule.medication_name}"
                    if schedule
                    else "Missed dose"
                ),
                payload={
                    "reminder_id": reminder.id,
                    "medication_name": schedule.medication_name if schedule else None,
                    "scheduled_for": reminder.scheduled_for.isoformat(),
                },
                related_reminder_id=reminder.id,
                related_medication_id=reminder.medication_schedule_id,
                commit=False,
            )
            missed += 1
        self.db.commit()
        return missed

    # ----- queries ------------------------------------------------------

    def list_for_patient(self, patient_id: int, *, limit: int = 200) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.patient_id == patient_id)
            .order_by(Reminder.scheduled_for.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
