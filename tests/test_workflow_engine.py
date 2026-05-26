"""Tests for the deterministic escalation rules engine."""
from app.ai.providers import CONFIDENCE_REVIEW_THRESHOLD
from app.core.event_types import EventType, Urgency
from app.models.alert import Alert, AlertStatus
from app.models.escalation import Escalation
from app.services.timeline import TimelineService


def _count(db, model):
    return db.query(model).count()


def test_single_missed_dose_raises_medium_alert(db, patient_id):
    TimelineService(db).record(
        patient_id=patient_id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        summary="Missed Metformin",
        payload={"medication_name": "Metformin"},
    )
    alerts = db.query(Alert).all()
    assert len(alerts) == 1
    assert alerts[0].urgency == Urgency.MEDIUM
    assert _count(db, Escalation) == 0


def test_two_misses_in_24h_triggers_high_alert_and_escalation(db, patient_id):
    svc = TimelineService(db)
    svc.record(
        patient_id=patient_id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        payload={"medication_name": "Insulin"},
    )
    svc.record(
        patient_id=patient_id,
        event_type=EventType.MEDICATION_MISSED,
        urgency=Urgency.MEDIUM,
        payload={"medication_name": "Insulin"},
    )

    high_alerts = (
        db.query(Alert).filter(Alert.urgency == Urgency.HIGH).all()
    )
    assert len(high_alerts) >= 1, "second miss in 24h must raise a HIGH alert"

    escalations = db.query(Escalation).all()
    assert len(escalations) == 1
    assert escalations[0].rule == "medication_missed_twice_in_24h"


def test_abnormal_reading_raises_alert_at_reported_urgency(db, patient_id):
    TimelineService(db).record(
        patient_id=patient_id,
        event_type=EventType.ABNORMAL_READING_DETECTED,
        urgency=Urgency.HIGH,
        summary="Glucose 320 mg/dL",
        payload={"detail": "glucose=320"},
    )
    alerts = db.query(Alert).all()
    assert len(alerts) == 1
    assert alerts[0].urgency == Urgency.HIGH


def test_low_confidence_document_marks_review_required(db, patient_id):
    low = CONFIDENCE_REVIEW_THRESHOLD - 0.1
    TimelineService(db).record(
        patient_id=patient_id,
        event_type=EventType.DOCUMENT_OCR_COMPLETED,
        summary="OCR done",
        confidence=low,
    )
    alerts = db.query(Alert).all()
    assert any("review" in a.title.lower() for a in alerts), (
        "low-confidence OCR must produce a review alert"
    )


def test_high_confidence_document_no_review(db, patient_id):
    high = CONFIDENCE_REVIEW_THRESHOLD + 0.2
    TimelineService(db).record(
        patient_id=patient_id,
        event_type=EventType.DOCUMENT_OCR_COMPLETED,
        summary="OCR done",
        confidence=high,
    )
    assert _count(db, Alert) == 0


def test_alert_resolution_records_event(db, patient_id):
    from app.services.alerts import AlertService

    TimelineService(db).record(
        patient_id=patient_id,
        event_type=EventType.SYMPTOM_REPORTED,
        summary="dizziness",
    )
    alert = db.query(Alert).first()
    assert alert is not None
    AlertService(db).resolve_alert(alert_id=alert.id)
    db.refresh(alert)
    assert alert.status == AlertStatus.RESOLVED
