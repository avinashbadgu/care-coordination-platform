from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_types import EventType, Urgency
from app.models.alert import Alert, AlertStatus
from app.models.base import utcnow


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def raise_alert(
        self,
        *,
        patient_id: int,
        urgency: Urgency,
        title: str,
        detail: str | None = None,
        source_event_id: int | None = None,
        commit: bool = True,
    ) -> Alert:
        from app.services.timeline import TimelineService

        alert = Alert(
            patient_id=patient_id,
            urgency=urgency,
            title=title,
            detail=detail,
            source_event_id=source_event_id,
            status=AlertStatus.OPEN,
        )
        self.db.add(alert)
        self.db.flush()

        TimelineService(self.db).record(
            patient_id=patient_id,
            event_type=EventType.ALERT_RAISED,
            urgency=urgency,
            summary=title,
            payload={"alert_id": alert.id, "detail": detail},
            commit=False,
            skip_engine=True,  # avoid rule re-entry from raise_alert itself
        )

        if commit:
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def resolve_alert(
        self,
        *,
        alert_id: int,
        resolved_by_caregiver_id: int | None = None,
        commit: bool = True,
    ) -> Alert | None:
        from app.services.timeline import TimelineService

        alert = self.db.get(Alert, alert_id)
        if alert is None or alert.status == AlertStatus.RESOLVED:
            return alert
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = utcnow()
        alert.resolved_by_caregiver_id = resolved_by_caregiver_id
        self.db.flush()

        TimelineService(self.db).record(
            patient_id=alert.patient_id,
            event_type=EventType.ALERT_RESOLVED,
            urgency=Urgency.LOW,
            summary=f"Alert resolved: {alert.title}",
            payload={"alert_id": alert.id},
            actor_caregiver_id=resolved_by_caregiver_id,
            commit=False,
            skip_engine=True,
        )

        if commit:
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def list_for_patient(
        self, *, patient_id: int, only_open: bool = False
    ) -> list[Alert]:
        stmt = select(Alert).where(Alert.patient_id == patient_id)
        if only_open:
            stmt = stmt.where(Alert.status != AlertStatus.RESOLVED)
        stmt = stmt.order_by(Alert.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())
