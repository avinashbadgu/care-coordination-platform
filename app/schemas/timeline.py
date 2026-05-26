from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.event_types import EventType, Urgency
from app.schemas.common import ORMModel


class TimelineEventCreate(BaseModel):
    event_type: EventType
    urgency: Urgency = Urgency.LOW
    occurred_at: datetime | None = None
    summary: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] | None = None
    source: str = "system"
    actor_caregiver_id: int | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    related_medication_id: int | None = None
    related_reminder_id: int | None = None
    related_document_id: int | None = None
    related_voice_note_id: int | None = None


class TimelineEventRead(ORMModel):
    id: int
    patient_id: int
    event_type: str
    urgency: Urgency
    occurred_at: datetime
    summary: str | None
    payload: dict[str, Any] | None
    source: str
    actor_caregiver_id: int | None
    confidence: float | None
    related_medication_id: int | None
    related_reminder_id: int | None
    related_document_id: int | None
    related_voice_note_id: int | None
    created_at: datetime
