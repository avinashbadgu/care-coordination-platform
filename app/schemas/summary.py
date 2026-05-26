from datetime import date, datetime
from typing import Any

from app.schemas.common import ORMModel


class DailySummaryRead(ORMModel):
    id: int
    patient_id: int
    summary_date: date
    headline: str | None
    body: str
    metrics: dict[str, Any] | None
    prompt_version: str | None
    created_at: datetime
    updated_at: datetime
