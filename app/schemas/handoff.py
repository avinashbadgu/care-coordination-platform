from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HandoffSummary(BaseModel):
    patient_id: int
    window_start: datetime
    window_end: datetime
    headline: str
    body: str
    events: dict[str, int]
    open_alerts: int
    open_escalations: int
    metrics: dict[str, Any]
