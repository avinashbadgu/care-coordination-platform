from __future__ import annotations

from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DailySummary(Base, TimestampMixin):
    __tablename__ = "daily_summaries"
    __table_args__ = (UniqueConstraint("patient_id", "summary_date", name="uq_daily_summary"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary_date: Mapped[date] = mapped_column(Date, nullable=False)

    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
