from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date | None = None
    timezone: str = "Asia/Kolkata"
    notes: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    date_of_birth: date | None = None
    timezone: str | None = None
    notes: str | None = None


class PatientRead(ORMModel):
    id: int
    full_name: str
    date_of_birth: date | None
    timezone: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
