from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.care_plan import (
    CarePlanCreate,
    CarePlanRead,
    CarePlanTaskCompletion,
    CarePlanTaskCreate,
    CarePlanTaskRead,
)
from app.services.care_plans import CarePlanService

router = APIRouter(tags=["care-plans"])


@router.post(
    "/patients/{patient_id}/care-plans",
    response_model=CarePlanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_care_plan(
    data: CarePlanCreate,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> CarePlanRead:
    plan = CarePlanService(db).create(patient_id=patient.id, data=data)
    plan = CarePlanService(db).get(plan.id)
    return CarePlanRead.model_validate(plan)


@router.get(
    "/patients/{patient_id}/care-plans",
    response_model=list[CarePlanRead],
)
def list_care_plans(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[CarePlanRead]:
    items = CarePlanService(db).list_for_patient(patient.id)
    return [CarePlanRead.model_validate(p) for p in items]


@router.post(
    "/care-plans/{care_plan_id}/tasks",
    response_model=CarePlanTaskRead,
    status_code=status.HTTP_201_CREATED,
)
def add_task(
    care_plan_id: int,
    data: CarePlanTaskCreate,
    db: Session = Depends(get_db),
) -> CarePlanTaskRead:
    plan = CarePlanService(db).get(care_plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="care plan not found")
    task = CarePlanService(db).add_task(care_plan_id=care_plan_id, data=data)
    return CarePlanTaskRead.model_validate(task)


@router.post(
    "/care-plans/{care_plan_id}/tasks/{task_id}/complete",
    response_model=CarePlanTaskRead,
)
def complete_task(
    care_plan_id: int,
    task_id: int,
    data: CarePlanTaskCompletion,
    db: Session = Depends(get_db),
) -> CarePlanTaskRead:
    task = CarePlanService(db).complete_task(
        care_plan_id=care_plan_id, task_id=task_id, data=data
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return CarePlanTaskRead.model_validate(task)
