from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.base import utcnow
from app.models.timeline import TimelineEvent


class TimelineService:
    """Single chokepoint for recording and querying timeline events.

    Every code path that produces a meaningful operational fact should go
    through `record()` — this keeps the timeline auditable, debuggable, and
    the single source of truth. The deterministic workflow engine is invoked
    automatically on each new event (unless `skip_engine=True`), so escalations
    and alerts are wired in by data, not by ad-hoc calls.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        *,
        patient_id: int,
        event_type: EventType,
        urgency: Urgency = Urgency.LOW,
        summary: str | None = None,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        source: str = "system",
        actor_caregiver_id: int | None = None,
        confidence: float | None = None,
        related_medication_id: int | None = None,
        related_reminder_id: int | None = None,
        related_document_id: int | None = None,
        related_voice_note_id: int | None = None,
        commit: bool = True,
        skip_engine: bool = False,
    ) -> TimelineEvent:
        event = TimelineEvent(
            patient_id=patient_id,
            event_type=event_type.value,
            urgency=urgency,
            summary=summary,
            payload=payload,
            occurred_at=occurred_at or utcnow(),
            source=source,
            actor_caregiver_id=actor_caregiver_id,
            confidence=confidence,
            related_medication_id=related_medication_id,
            related_reminder_id=related_reminder_id,
            related_document_id=related_document_id,
            related_voice_note_id=related_voice_note_id,
        )
        self.db.add(event)
        self.db.flush()

        if not skip_engine:
            # Imported lazily to keep the service layer cycle-free.
            from app.workflows.engine import get_engine

            get_engine().on_event(self.db, event)

        if commit:
            self.db.commit()
            self.db.refresh(event)
        return event

    def list_for_patient(
        self,
        *,
        patient_id: int,
        limit: int = 100,
        offset: int = 0,
        event_types: list[EventType] | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        urgencies: list[Urgency] | None = None,
        actor_caregiver_id: int | None = None,
        source: str | None = None,
    ) -> tuple[list[TimelineEvent], int]:
        stmt = select(TimelineEvent).where(TimelineEvent.patient_id == patient_id)
        if event_types:
            stmt = stmt.where(
                TimelineEvent.event_type.in_([et.value for et in event_types])
            )
        if since is not None:
            stmt = stmt.where(TimelineEvent.occurred_at >= since)
        if until is not None:
            stmt = stmt.where(TimelineEvent.occurred_at <= until)
        if urgencies:
            stmt = stmt.where(TimelineEvent.urgency.in_(urgencies))
        if actor_caregiver_id is not None:
            stmt = stmt.where(TimelineEvent.actor_caregiver_id == actor_caregiver_id)
        if source is not None:
            stmt = stmt.where(TimelineEvent.source == source)

        count_stmt = stmt.with_only_columns(TimelineEvent.id).order_by(None)
        total = len(self.db.execute(count_stmt).all())

        stmt = stmt.order_by(TimelineEvent.occurred_at.desc()).limit(limit).offset(offset)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total
