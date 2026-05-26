from __future__ import annotations

from enum import StrEnum

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class VoiceNoteStatus(StrEnum):
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    EXTRACTED = "extracted"
    FAILED = "failed"


class VoiceNote(Base, TimestampMixin):
    __tablename__ = "voice_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_by_caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True
    )

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)

    status: Mapped[VoiceNoteStatus] = mapped_column(
        String(32), default=VoiceNoteStatus.UPLOADED, nullable=False
    )

    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
