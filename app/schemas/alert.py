from datetime import datetime

from pydantic import BaseModel, Field

from app.core.event_types import Urgency
from app.models.alert import AlertStatus
from app.schemas.common import ORMModel


class AlertCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    detail: str | None = None
    urgency: Urgency = Urgency.MEDIUM


class AlertRead(ORMModel):
    id: int
    patient_id: int
    urgency: Urgency
    title: str
    detail: str | None
    status: AlertStatus
    resolved_at: datetime | None
    resolved_by_caregiver_id: int | None
    source_event_id: int | None
    created_at: datetime
    updated_at: datetime


class AlertResolve(BaseModel):
    resolved_by_caregiver_id: int | None = None
