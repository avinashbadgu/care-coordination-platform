from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.event_types import Urgency
from app.models.base import Base, TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.patient import Patient


class TimelineEvent(Base, TimestampMixin):
    """Canonical operational event log. The timeline is the source of truth.

    Every meaningful action becomes a typed event so the system is debuggable
    and auditable from timeline history alone.
    """

    __tablename__ = "timeline_events"
    __table_args__ = (
        Index("ix_timeline_patient_occurred", "patient_id", "occurred_at"),
        Index("ix_timeline_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    urgency: Mapped[Urgency] = mapped_column(String(16), default=Urgency.LOW, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # Free-text human-readable summary; structured details live in payload.
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Attribution: who/what generated this event (caregiver or "system").
    source: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    actor_caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True
    )

    # AI confidence (0..1) when the event was produced by an AI pipeline.
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Optional reverse-links for traceability into the originating record.
    related_medication_id: Mapped[int | None] = mapped_column(
        ForeignKey("medication_schedules.id", ondelete="SET NULL"), nullable=True
    )
    related_reminder_id: Mapped[int | None] = mapped_column(
        ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True
    )
    related_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploaded_documents.id", ondelete="SET NULL"), nullable=True
    )
    related_voice_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("voice_notes.id", ondelete="SET NULL"), nullable=True
    )

    patient: Mapped[Patient] = relationship(back_populates="timeline_events")
