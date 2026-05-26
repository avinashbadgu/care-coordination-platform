"""Shift-handoff summaries.

Generates an operational summary of a time window (e.g. night caregiver →
morning caregiver) directly from the timeline. Deterministic counts; the AI
provider supplies the prose. Designed for the real-world handoff problem:
"what do I need to know about the last 8 hours?".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import AIProvider, get_ai_provider
from app.models.alert import Alert, AlertStatus
from app.models.escalation import Escalation, EscalationStatus
from app.models.patient import Patient
from app.models.timeline import TimelineEvent


class HandoffService:
    def __init__(self, db: Session, *, ai: AIProvider | None = None) -> None:
        self.db = db
        self.ai = ai or get_ai_provider()

    def generate(
        self,
        *,
        patient_id: int,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
        hours: int = 12,
    ) -> dict[str, Any]:
        patient = self.db.get(Patient, patient_id)
        if patient is None:
            raise ValueError(f"patient {patient_id} not found")

        window_end = window_end or datetime.now(timezone.utc)
        window_start = window_start or (window_end - timedelta(hours=hours))

        events = list(
            self.db.execute(
                select(TimelineEvent)
                .where(
                    TimelineEvent.patient_id == patient_id,
                    TimelineEvent.occurred_at >= window_start,
                    TimelineEvent.occurred_at <= window_end,
                )
                .order_by(TimelineEvent.occurred_at.asc())
            ).scalars()
        )

        counts: dict[str, int] = {}
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1

        open_alerts = (
            self.db.execute(
                select(Alert)
                .where(
                    Alert.patient_id == patient_id,
                    Alert.status != AlertStatus.RESOLVED,
                )
            )
            .scalars()
            .all()
        )
        open_escalations = (
            self.db.execute(
                select(Escalation)
                .where(
                    Escalation.patient_id == patient_id,
                    Escalation.status != EscalationStatus.RESOLVED,
                )
            )
            .scalars()
            .all()
        )

        taken = counts.get("medication_taken", 0)
        missed = counts.get("medication_missed", 0)
        adherence = taken / (taken + missed) if (taken + missed) else None

        lines: list[str] = [
            f"Patient: {patient.full_name}",
            f"Window: {window_start.isoformat()} → {window_end.isoformat()}",
            f"Medications taken: {taken}",
            f"Medications missed: {missed}",
            f"Open alerts: {len(open_alerts)}",
            f"Open escalations: {len(open_escalations)}",
        ]
        if missed:
            lines.append("Action: review missed doses and confirm follow-up.")
        if len(open_escalations) > 0:
            lines.append("Action: resolve or escalate outstanding incidents.")

        headline = (
            f"{taken} taken / {missed} missed · "
            f"{len(open_alerts)} open alerts · {len(open_escalations)} open escalations"
        )

        return {
            "patient_id": patient_id,
            "window_start": window_start,
            "window_end": window_end,
            "headline": headline,
            "body": "\n".join(lines),
            "events": counts,
            "open_alerts": len(open_alerts),
            "open_escalations": len(open_escalations),
            "metrics": {
                "adherence_ratio": adherence,
                "event_total": len(events),
            },
        }
