from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CarePlanTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    cadence: str | None = Field(default=None, max_length=64)
    instructions: str | None = None


class CarePlanTaskRead(ORMModel):
    id: int
    care_plan_id: int
    title: str
    cadence: str | None
    instructions: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class CarePlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    created_by_caregiver_id: int | None = None
    tasks: list[CarePlanTaskCreate] = Field(default_factory=list)


class CarePlanRead(ORMModel):
    id: int
    patient_id: int
    title: str
    description: str | None
    starts_on: date | None
    ends_on: date | None
    created_by_caregiver_id: int | None
    active: bool
    created_at: datetime
    updated_at: datetime
    tasks: list[CarePlanTaskRead] = Field(default_factory=list)


class CarePlanTaskCompletion(BaseModel):
    completed_by_caregiver_id: int | None = None
    notes: str | None = None
