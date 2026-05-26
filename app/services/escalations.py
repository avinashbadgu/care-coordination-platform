from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.base import utcnow
from app.models.escalation import Escalation, EscalationStatus


class EscalationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def trigger(
        self,
        *,
        patient_id: int,
        rule: str,
        reason: str | None = None,
        alert_id: int | None = None,
        notified_caregiver_id: int | None = None,
        commit: bool = True,
    ) -> Escalation:
        from app.services.timeline import TimelineService

        escalation = Escalation(
            patient_id=patient_id,
            rule=rule,
            reason=reason,
            alert_id=alert_id,
            status=EscalationStatus.OPEN,
            notified_caregiver_id=notified_caregiver_id,
            notified_at=utcnow() if notified_caregiver_id else None,
        )
        self.db.add(escalation)
        self.db.flush()

        TimelineService(self.db).record(
            patient_id=patient_id,
            event_type=EventType.ESCALATION_TRIGGERED,
            urgency=Urgency.HIGH,
            summary=f"Escalation: {rule}",
            payload={
                "escalation_id": escalation.id,
                "rule": rule,
                "reason": reason,
                "alert_id": alert_id,
                "notified_caregiver_id": notified_caregiver_id,
            },
            commit=False,
            skip_engine=True,
        )

        if commit:
            self.db.commit()
            self.db.refresh(escalation)
        return escalation

    def resolve(
        self,
        *,
        escalation_id: int,
        commit: bool = True,
    ) -> Escalation | None:
        from app.services.timeline import TimelineService

        escalation = self.db.get(Escalation, escalation_id)
        if escalation is None or escalation.status == EscalationStatus.RESOLVED:
            return escalation
        escalation.status = EscalationStatus.RESOLVED
        escalation.resolved_at = utcnow()
        self.db.flush()

        TimelineService(self.db).record(
            patient_id=escalation.patient_id,
            event_type=EventType.ESCALATION_RESOLVED,
            urgency=Urgency.LOW,
            summary=f"Escalation resolved: {escalation.rule}",
            payload={"escalation_id": escalation.id},
            commit=False,
            skip_engine=True,
        )

        if commit:
            self.db.commit()
            self.db.refresh(escalation)
        return escalation

    def list_for_patient(self, patient_id: int) -> list[Escalation]:
        stmt = (
            select(Escalation)
            .where(Escalation.patient_id == patient_id)
            .order_by(Escalation.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
