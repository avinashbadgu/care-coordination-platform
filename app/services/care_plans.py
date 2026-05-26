from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.event_types import EventType
from app.models.care_plan import CarePlan, CarePlanTask
from app.schemas.care_plan import (
    CarePlanCreate,
    CarePlanTaskCompletion,
    CarePlanTaskCreate,
)
from app.services.timeline import TimelineService


class CarePlanService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.timeline = TimelineService(db)

    def create(self, *, patient_id: int, data: CarePlanCreate) -> CarePlan:
        plan = CarePlan(
            patient_id=patient_id,
            title=data.title,
            description=data.description,
            starts_on=data.starts_on,
            ends_on=data.ends_on,
            created_by_caregiver_id=data.created_by_caregiver_id,
        )
        self.db.add(plan)
        self.db.flush()

        for task_data in data.tasks:
            self.db.add(
                CarePlanTask(
                    care_plan_id=plan.id,
                    title=task_data.title,
                    cadence=task_data.cadence,
                    instructions=task_data.instructions,
                )
            )
        self.db.flush()

        self.timeline.record(
            patient_id=patient_id,
            event_type=EventType.CARE_PLAN_CREATED,
            summary=f"Care plan created: {plan.title}",
            payload={"care_plan_id": plan.id, "task_count": len(data.tasks)},
            actor_caregiver_id=data.created_by_caregiver_id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def add_task(self, *, care_plan_id: int, data: CarePlanTaskCreate) -> CarePlanTask:
        task = CarePlanTask(care_plan_id=care_plan_id, **data.model_dump(exclude_none=True))
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def complete_task(
        self, *, care_plan_id: int, task_id: int, data: CarePlanTaskCompletion
    ) -> CarePlanTask | None:
        task = self.db.get(CarePlanTask, task_id)
        if task is None or task.care_plan_id != care_plan_id:
            return None
        plan = self.db.get(CarePlan, care_plan_id)
        if plan is None:
            return None

        self.timeline.record(
            patient_id=plan.patient_id,
            event_type=EventType.CARE_PLAN_TASK_COMPLETED,
            summary=f"Care plan task completed: {task.title}",
            payload={
                "care_plan_id": plan.id,
                "task_id": task.id,
                "notes": data.notes,
            },
            actor_caregiver_id=data.completed_by_caregiver_id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, care_plan_id: int) -> CarePlan | None:
        stmt = (
            select(CarePlan)
            .where(CarePlan.id == care_plan_id)
            .options(selectinload(CarePlan.tasks))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_patient(self, patient_id: int) -> list[CarePlan]:
        stmt = (
            select(CarePlan)
            .where(CarePlan.patient_id == patient_id)
            .options(selectinload(CarePlan.tasks))
            .order_by(CarePlan.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
