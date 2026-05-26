from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import AIProvider, get_ai_provider
from app.core.event_types import EventType, Urgency
from app.models.patient import Patient
from app.models.summary import DailySummary
from app.models.timeline import TimelineEvent
from app.services.timeline import TimelineService


class SummaryService:
    def __init__(self, db: Session, *, ai: AIProvider | None = None) -> None:
        self.db = db
        self.ai = ai or get_ai_provider()
        self.timeline = TimelineService(db)

    def generate(self, *, patient_id: int, target_date: date | None = None) -> DailySummary:
        patient = self.db.get(Patient, patient_id)
        if patient is None:
            raise ValueError(f"patient {patient_id} not found")
        tz = ZoneInfo(patient.timezone)
        target_date = target_date or datetime.now(tz).date()

        # Day window in patient's local time → UTC for query.
        start_local = datetime.combine(target_date, time.min).replace(tzinfo=tz)
        end_local = datetime.combine(target_date, time.max).replace(tzinfo=tz)
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        events = list(
            self.db.execute(
                select(TimelineEvent)
                .where(
                    TimelineEvent.patient_id == patient_id,
                    TimelineEvent.occurred_at >= start_utc,
                    TimelineEvent.occurred_at <= end_utc,
                )
                .order_by(TimelineEvent.occurred_at.asc())
            ).scalars()
        )

        result = self.ai.summarize_day(
            patient_name=patient.full_name,
            summary_date=target_date,
            events=[
                {
                    "event_type": e.event_type,
                    "urgency": e.urgency,
                    "summary": e.summary,
                    "occurred_at": e.occurred_at.isoformat(),
                }
                for e in events
            ],
        )

        # Upsert by (patient_id, summary_date).
        existing = self.db.execute(
            select(DailySummary).where(
                DailySummary.patient_id == patient_id,
                DailySummary.summary_date == target_date,
            )
        ).scalar_one_or_none()
        if existing:
            existing.headline = result.headline
            existing.body = result.body
            existing.metrics = result.metrics
            existing.prompt_version = result.prompt_version
            summary_row = existing
        else:
            summary_row = DailySummary(
                patient_id=patient_id,
                summary_date=target_date,
                headline=result.headline,
                body=result.body,
                metrics=result.metrics,
                prompt_version=result.prompt_version,
            )
            self.db.add(summary_row)
        self.db.flush()

        self.timeline.record(
            patient_id=patient_id,
            event_type=EventType.DAILY_SUMMARY_GENERATED,
            urgency=Urgency.LOW,
            summary=result.headline,
            payload={
                "summary_id": summary_row.id,
                "summary_date": target_date.isoformat(),
                "metrics": result.metrics,
            },
            commit=False,
        )
        self.db.commit()
        self.db.refresh(summary_row)
        return summary_row

    def list_for_patient(self, patient_id: int, *, limit: int = 30) -> list[DailySummary]:
        stmt = (
            select(DailySummary)
            .where(DailySummary.patient_id == patient_id)
            .order_by(DailySummary.summary_date.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
