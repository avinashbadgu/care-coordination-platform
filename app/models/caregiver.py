from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.event_types import CaregiverRole
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class Caregiver(Base, TimestampMixin):
    __tablename__ = "caregivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    patient_links: Mapped[list[PatientCaregiver]] = relationship(
        back_populates="caregiver", cascade="all, delete-orphan"
    )


class PatientCaregiver(Base, TimestampMixin):
    """Association: caregiver-of-patient with a role.

    A caregiver may be linked to multiple patients (e.g., a nurse covering
    several patients) with potentially different roles.
    """

    __tablename__ = "patient_caregivers"
    __table_args__ = (
        UniqueConstraint("patient_id", "caregiver_id", "role", name="uq_patient_caregiver_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    caregiver_id: Mapped[int] = mapped_column(
        ForeignKey("caregivers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[CaregiverRole] = mapped_column(String(32), nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="caregiver_links")
    caregiver: Mapped[Caregiver] = relationship(back_populates="patient_links")
