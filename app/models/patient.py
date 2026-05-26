from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.care_plan import CarePlan
    from app.models.caregiver import PatientCaregiver
    from app.models.medication import MedicationSchedule
    from app.models.timeline import TimelineEvent


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    timeline_events: Mapped[list[TimelineEvent]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    care_plans: Mapped[list[CarePlan]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    medication_schedules: Mapped[list[MedicationSchedule]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
    caregiver_links: Mapped[list[PatientCaregiver]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )
