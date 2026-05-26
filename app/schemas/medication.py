import re
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class MedicationScheduleCreate(BaseModel):
    medication_name: str = Field(min_length=1, max_length=255)
    dosage: str | None = Field(default=None, max_length=64)
    instructions: str | None = None
    times_of_day: list[str] = Field(default_factory=list)
    starts_on: date | None = None
    ends_on: date | None = None

    @field_validator("times_of_day")
    @classmethod
    def _validate_times(cls, v: list[str]) -> list[str]:
        for t in v:
            if not _TIME_RE.match(t):
                raise ValueError(f"times_of_day entries must be HH:MM 24h, got {t!r}")
        return v


class MedicationScheduleRead(ORMModel):
    id: int
    patient_id: int
    medication_name: str
    dosage: str | None
    instructions: str | None
    times_of_day: list[str]
    starts_on: date | None
    ends_on: date | None
    active: bool
    created_at: datetime
    updated_at: datetime
