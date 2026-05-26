from datetime import datetime

from pydantic import BaseModel, Field

from app.core.event_types import CaregiverRole
from app.schemas.common import ORMModel


class CaregiverCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    # Plain str for MVP; swap for pydantic.EmailStr once `pydantic[email]` is
    # added to deps if strict RFC 5322 validation becomes worth the cost.
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class CaregiverRead(ORMModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    created_at: datetime
    updated_at: datetime


class PatientCaregiverLinkCreate(BaseModel):
    caregiver_id: int
    role: CaregiverRole


class PatientCaregiverLinkRead(ORMModel):
    id: int
    patient_id: int
    caregiver_id: int
    role: CaregiverRole
    created_at: datetime
