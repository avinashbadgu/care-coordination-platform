from datetime import datetime

from app.models.escalation import EscalationStatus
from app.schemas.common import ORMModel


class EscalationRead(ORMModel):
    id: int
    patient_id: int
    alert_id: int | None
    rule: str | None
    reason: str | None
    status: EscalationStatus
    notified_caregiver_id: int | None
    notified_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
