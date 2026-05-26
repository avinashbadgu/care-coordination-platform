"""Deterministic workflow engine that reacts to timeline events.

Hooked into `TimelineService.record()` so every meaningful action runs the
rule set. Rules are pure functions: they read recent timeline state and
decide whether to raise alerts or trigger escalations. AI never controls
these — they are intentionally simple and auditable.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.base import utcnow
from app.models.timeline import TimelineEvent

if TYPE_CHECKING:
    from app.models.timeline import TimelineEvent as TimelineEventT  # noqa: F401

log = logging.getLogger(__name__)


# A rule takes (db, triggering_event) and applies any side effects directly
# (creating alerts / escalations via their services with commit=False so they
# join the outer transaction).
Rule = Callable[[Session, TimelineEvent], None]


def _recent_events(
    db: Session,
    *,
    patient_id: int,
    event_type: EventType,
    within: timedelta,
) -> list[TimelineEvent]:
    cutoff = utcnow() - within
    stmt = (
        select(TimelineEvent)
        .where(
            TimelineEvent.patient_id == patient_id,
            TimelineEvent.event_type == event_type.value,
            TimelineEvent.occurred_at >= cutoff,
        )
        .order_by(TimelineEvent.occurred_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


# --- rules ---------------------------------------------------------------

def rule_missed_medication(db: Session, event: TimelineEvent) -> None:
    """A single missed dose notifies caregivers; two in 24h escalates."""
    if event.event_type != EventType.MEDICATION_MISSED.value:
        return

    from app.services.alerts import AlertService
    from app.services.escalations import EscalationService

    missed_recent = _recent_events(
        db,
        patient_id=event.patient_id,
        event_type=EventType.MEDICATION_MISSED,
        within=timedelta(hours=24),
    )

    med_name = (event.payload or {}).get("medication_name") or "medication"

    if len(missed_recent) >= 2:
        alert = AlertService(db).raise_alert(
            patient_id=event.patient_id,
            urgency=Urgency.HIGH,
            title=f"Two missed doses of {med_name} in 24h",
            detail="Two or more missed doses detected within 24 hours.",
            source_event_id=event.id,
            commit=False,
        )
        EscalationService(db).trigger(
            patient_id=event.patient_id,
            rule="medication_missed_twice_in_24h",
            reason=f"{len(missed_recent)} missed doses of {med_name} within 24h",
            alert_id=alert.id,
            commit=False,
        )
    else:
        AlertService(db).raise_alert(
            patient_id=event.patient_id,
            urgency=Urgency.MEDIUM,
            title=f"Missed dose: {med_name}",
            detail="One missed dose recorded — caregiver should follow up.",
            source_event_id=event.id,
            commit=False,
        )


def rule_abnormal_reading(db: Session, event: TimelineEvent) -> None:
    """Abnormal readings always raise an alert at their reported urgency."""
    if event.event_type != EventType.ABNORMAL_READING_DETECTED.value:
        return

    from app.services.alerts import AlertService

    AlertService(db).raise_alert(
        patient_id=event.patient_id,
        urgency=event.urgency or Urgency.MEDIUM,
        title=event.summary or "Abnormal reading detected",
        detail=str((event.payload or {}).get("detail") or ""),
        source_event_id=event.id,
        commit=False,
    )


def rule_low_confidence_document(db: Session, event: TimelineEvent) -> None:
    """OCR/extraction below the review threshold must be flagged."""
    if event.event_type != EventType.DOCUMENT_OCR_COMPLETED.value:
        return
    confidence = event.confidence
    if confidence is None:
        return

    from app.ai.providers import CONFIDENCE_REVIEW_THRESHOLD
    from app.services.alerts import AlertService
    from app.services.timeline import TimelineService

    if confidence < CONFIDENCE_REVIEW_THRESHOLD:
        TimelineService(db).record(
            patient_id=event.patient_id,
            event_type=EventType.DOCUMENT_REVIEW_REQUIRED,
            urgency=Urgency.MEDIUM,
            summary="Document extraction below confidence threshold",
            payload={"confidence": confidence, "source_event_id": event.id},
            commit=False,
            skip_engine=True,
        )
        AlertService(db).raise_alert(
            patient_id=event.patient_id,
            urgency=Urgency.MEDIUM,
            title="Document needs human review",
            detail=f"OCR/extraction confidence {confidence:.2f} below threshold.",
            source_event_id=event.id,
            commit=False,
        )


def rule_symptom_reported(db: Session, event: TimelineEvent) -> None:
    """A reported symptom raises a medium alert by default."""
    if event.event_type != EventType.SYMPTOM_REPORTED.value:
        return

    from app.services.alerts import AlertService

    AlertService(db).raise_alert(
        patient_id=event.patient_id,
        urgency=event.urgency or Urgency.MEDIUM,
        title=event.summary or "Symptom reported",
        detail=str((event.payload or {}).get("symptoms") or ""),
        source_event_id=event.id,
        commit=False,
    )


DEFAULT_RULES: list[Rule] = [
    rule_missed_medication,
    rule_abnormal_reading,
    rule_low_confidence_document,
    rule_symptom_reported,
]


class WorkflowEngine:
    """Runs deterministic rules against a triggering timeline event."""

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules if rules is not None else DEFAULT_RULES

    def on_event(self, db: Session, event: TimelineEvent) -> None:
        for rule in self.rules:
            try:
                rule(db, event)
            except Exception:  # noqa: BLE001
                # Rules must never break the originating write. Log and continue.
                log.exception(
                    "rule %s failed for event %s/%s",
                    rule.__name__, event.id, event.event_type,
                )


_engine: WorkflowEngine | None = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
