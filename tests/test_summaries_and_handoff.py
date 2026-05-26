from datetime import date

from app.core.event_types import EventType, Urgency
from app.services.summaries import SummaryService
from app.services.timeline import TimelineService


def test_summary_counts_events_and_computes_adherence(db, patient_id):
    svc = TimelineService(db)
    svc.record(patient_id=patient_id, event_type=EventType.MEDICATION_TAKEN)
    svc.record(patient_id=patient_id, event_type=EventType.MEDICATION_TAKEN)
    svc.record(
        patient_id=patient_id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        payload={"medication_name": "Insulin"},
    )

    summary = SummaryService(db).generate(
        patient_id=patient_id, target_date=date.today()
    )
    assert summary.id is not None
    metrics = summary.metrics or {}
    counts = metrics.get("event_counts") or {}
    assert counts.get(EventType.MEDICATION_TAKEN.value) == 2
    assert counts.get(EventType.MEDICATION_MISSED.value) == 1
    assert metrics.get("adherence_ratio") == 2 / 3


def test_summary_upsert_by_date(db, patient_id):
    svc = SummaryService(db)
    first = svc.generate(patient_id=patient_id, target_date=date.today())
    second = svc.generate(patient_id=patient_id, target_date=date.today())
    assert first.id == second.id, "second call on same date must update in place"
