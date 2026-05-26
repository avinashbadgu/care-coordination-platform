from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class CarePlan(Base, TimestampMixin):
    __tablename__ = "care_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_caregiver_id: Mapped[int | None] = mapped_column(
        ForeignKey("caregivers.id", ondelete="SET NULL"), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="care_plans")
    tasks: Mapped[list[CarePlanTask]] = relationship(
        back_populates="care_plan", cascade="all, delete-orphan"
    )


class CarePlanTask(Base, TimestampMixin):
    """A discrete, trackable task inside a care plan (non-medication)."""

    __tablename__ = "care_plan_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    care_plan_id: Mapped[int] = mapped_column(
        ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    cadence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    care_plan: Mapped[CarePlan] = relationship(back_populates="tasks")
