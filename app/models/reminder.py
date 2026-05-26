from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ReminderStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    MISSED = "missed"
    FAILED = "failed"


class Reminder(Base, TimestampMixin):
    """Single reminder instance — one row per scheduled fire-time.

    The medication schedule expands into reminder rows ahead of time; the
    workflow engine then drives status transitions and timeline events.
    """

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("medication_schedules.id", ondelete="SET NULL"), nullable=True, index=True
    )

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    status: Mapped[ReminderStatus] = mapped_column(
        String(16), default=ReminderStatus.PENDING, nullable=False
    )
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
