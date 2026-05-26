from datetime import datetime

from pydantic import BaseModel

from app.models.reminder import ReminderStatus
from app.schemas.common import ORMModel


class ReminderRead(ORMModel):
    id: int
    patient_id: int
    medication_schedule_id: int | None
    scheduled_for: datetime
    sent_at: datetime | None
    acknowledged_at: datetime | None
    status: ReminderStatus
    channel: str | None
    retries: int
    created_at: datetime
    updated_at: datetime


class ReminderAck(BaseModel):
    acknowledged_by_caregiver_id: int | None = None
    notes: str | None = None
