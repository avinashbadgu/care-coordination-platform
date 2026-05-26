from datetime import datetime
from typing import Any

from app.models.voice_note import VoiceNoteStatus
from app.schemas.common import ORMModel


class VoiceNoteRead(ORMModel):
    id: int
    patient_id: int
    recorded_by_caregiver_id: int | None
    original_filename: str
    mime_type: str | None
    storage_path: str
    duration_seconds: float | None
    status: VoiceNoteStatus
    transcript: str | None
    extracted_entities: dict[str, Any] | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime
