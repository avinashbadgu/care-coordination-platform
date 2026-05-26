from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.base import utcnow
from app.models.medication import MedicationSchedule
from app.models.reminder import Reminder, ReminderStatus
from app.services.reminders import ReminderService


def _schedule(db, patient_id: int, times: list[str]) -> MedicationSchedule:
    schedule = MedicationSchedule(
        patient_id=patient_id,
        medication_name="Metformin",
        dosage="500mg",
        times_of_day=times,
        active=True,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def test_expand_creates_reminder_rows_for_each_time(db, patient_id):
    _schedule(db, patient_id, ["08:00", "20:00"])

    created = ReminderService(db).expand_for_patient(
        patient_id=patient_id, target_date=date(2026, 5, 25)
    )
    assert len(created) == 2
    # Patient tz is UTC so stored UTC hours match the schedule hours.
    # (SQLite returns naive datetimes; we don't rely on tzinfo here.)
    hours = sorted(r.scheduled_for.hour for r in created)
    assert hours == [8, 20]


def test_expand_is_idempotent(db, patient_id):
    _schedule(db, patient_id, ["08:00"])
    svc = ReminderService(db)
    target = date(2026, 5, 25)

    first = svc.expand_for_patient(patient_id=patient_id, target_date=target)
    second = svc.expand_for_patient(patient_id=patient_id, target_date=target)
    assert len(first) == 1
    assert len(second) == 0
    assert db.query(Reminder).count() == 1


def test_dispatch_sends_due_reminders_and_records_event(db, patient_id):
    _schedule(db, patient_id, ["08:00"])
    # Place a reminder in the past so dispatch picks it up.
    reminder = Reminder(
        patient_id=patient_id,
        scheduled_for=utcnow() - timedelta(minutes=5),
        status=ReminderStatus.PENDING,
    )
    db.add(reminder)
    db.commit()

    sent = ReminderService(db).dispatch_due()
    assert sent == 1
    db.refresh(reminder)
    assert reminder.status == ReminderStatus.SENT
    assert reminder.channel == "log"


def test_acknowledge_records_medication_taken(db, patient_id):
    schedule = _schedule(db, patient_id, ["08:00"])
    reminder = Reminder(
        patient_id=patient_id,
        medication_schedule_id=schedule.id,
        scheduled_for=utcnow() - timedelta(minutes=5),
        status=ReminderStatus.SENT,
    )
    db.add(reminder)
    db.commit()

    ReminderService(db).acknowledge(reminder_id=reminder.id)
    db.refresh(reminder)
    assert reminder.status == ReminderStatus.ACKNOWLEDGED

    from app.core.event_types import EventType
    from app.models.timeline import TimelineEvent

    types = {
        e.event_type
        for e in db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient_id).all()
    }
    assert EventType.MEDICATION_TAKEN.value in types
    assert EventType.REMINDER_ACKNOWLEDGED.value in types


def test_detect_misses_flags_unacknowledged_past_grace(db, patient_id):
    schedule = _schedule(db, patient_id, ["08:00"])
    old = Reminder(
        patient_id=patient_id,
        medication_schedule_id=schedule.id,
        scheduled_for=utcnow() - timedelta(hours=2),
        status=ReminderStatus.SENT,
    )
    fresh = Reminder(
        patient_id=patient_id,
        medication_schedule_id=schedule.id,
        scheduled_for=utcnow(),
        status=ReminderStatus.SENT,
    )
    db.add_all([old, fresh])
    db.commit()

    missed = ReminderService(db).detect_misses(grace=timedelta(hours=1))
    assert missed == 1
    db.refresh(old)
    db.refresh(fresh)
    assert old.status == ReminderStatus.MISSED
    assert fresh.status == ReminderStatus.SENT
