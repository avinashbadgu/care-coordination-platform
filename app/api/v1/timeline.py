from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.core.event_types import EventType, Urgency
from app.models.patient import Patient
from app.schemas.common import Page
from app.schemas.timeline import TimelineEventCreate, TimelineEventRead
from app.services.timeline import TimelineService

router = APIRouter(prefix="/patients/{patient_id}/timeline", tags=["timeline"])


@router.post("", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def record_event(
    data: TimelineEventCreate,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> TimelineEventRead:
    event = TimelineService(db).record(
        patient_id=patient.id,
        event_type=data.event_type,
        urgency=data.urgency,
        summary=data.summary,
        payload=data.payload,
        occurred_at=data.occurred_at,
        source=data.source,
        actor_caregiver_id=data.actor_caregiver_id,
        confidence=data.confidence,
        related_medication_id=data.related_medication_id,
        related_reminder_id=data.related_reminder_id,
        related_document_id=data.related_document_id,
        related_voice_note_id=data.related_voice_note_id,
    )
    return TimelineEventRead.model_validate(event)


@router.get("", response_model=Page[TimelineEventRead])
def list_events(
    patient: Patient = Depends(get_existing_patient),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_types: list[EventType] | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    urgency: list[Urgency] | None = Query(default=None),
    actor_caregiver_id: int | None = Query(default=None),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> Page[TimelineEventRead]:
    items, total = TimelineService(db).list_for_patient(
        patient_id=patient.id,
        limit=limit,
        offset=offset,
        event_types=event_types,
        since=since,
        until=until,
        urgencies=urgency,
        actor_caregiver_id=actor_caregiver_id,
        source=source,
    )
    return Page[TimelineEventRead](
        items=[TimelineEventRead.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )
