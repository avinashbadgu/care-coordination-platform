from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.event_types import Urgency
from app.models.base import Base, TimestampMixin


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    urgency: Mapped[Urgency] = mapped_column(String(16), default=Urgency.LOW, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[AlertStatus] = mapped_column(
        String(16), default=AlertStatus.OPEN, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True
    )

    # Trace back to the timeline event that triggered the alert (if any).
    source_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("timeline_events.id", ondelete="SET NULL"), nullable=True
    )
