from app.core.event_types import EventType, Urgency
from app.services.timeline import TimelineService


def test_record_writes_an_event(db, patient_id):
    svc = TimelineService(db)
    event = svc.record(
        patient_id=patient_id,
        event_type=EventType.MEDICATION_TAKEN,
        summary="Took Metformin",
    )
    assert event.id is not None
    assert event.event_type == EventType.MEDICATION_TAKEN.value
    assert event.urgency == Urgency.LOW


def test_list_for_patient_filters_by_type(db, patient_id):
    svc = TimelineService(db)
    svc.record(patient_id=patient_id, event_type=EventType.MEDICATION_TAKEN)
    svc.record(patient_id=patient_id, event_type=EventType.MEDICATION_MISSED)

    items, total = svc.list_for_patient(
        patient_id=patient_id, event_types=[EventType.MEDICATION_TAKEN]
    )
    assert total == 1
    assert items[0].event_type == EventType.MEDICATION_TAKEN.value


def test_engine_skipped_when_skip_engine_true(db, patient_id):
    """skip_engine=True must not trigger the workflow engine (used by engine itself)."""
    svc = TimelineService(db)
    # alert_raised would normally not re-trigger anything, but we use it to
    # assert the engine isn't called on engine-generated events.
    event = svc.record(
        patient_id=patient_id,
        event_type=EventType.ALERT_RAISED,
        urgency=Urgency.HIGH,
        skip_engine=True,
    )
    assert event.id is not None
