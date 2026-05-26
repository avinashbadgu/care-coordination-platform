from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.caregiver import (
    CaregiverCreate,
    CaregiverRead,
    PatientCaregiverLinkCreate,
    PatientCaregiverLinkRead,
)
from app.schemas.common import Page
from app.services.caregivers import CaregiverService

router = APIRouter(tags=["caregivers"])


@router.post("/caregivers", response_model=CaregiverRead, status_code=status.HTTP_201_CREATED)
def create_caregiver(data: CaregiverCreate, db: Session = Depends(get_db)) -> CaregiverRead:
    caregiver = CaregiverService(db).create(data)
    return CaregiverRead.model_validate(caregiver)


@router.get("/caregivers", response_model=Page[CaregiverRead])
def list_caregivers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[CaregiverRead]:
    items, total = CaregiverService(db).list(limit=limit, offset=offset)
    return Page[CaregiverRead](
        items=[CaregiverRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/patients/{patient_id}/caregivers",
    response_model=PatientCaregiverLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def link_caregiver(
    data: PatientCaregiverLinkCreate,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> PatientCaregiverLinkRead:
    link = CaregiverService(db).link_to_patient(patient_id=patient.id, data=data)
    return PatientCaregiverLinkRead.model_validate(link)


@router.get(
    "/patients/{patient_id}/caregivers",
    response_model=list[PatientCaregiverLinkRead],
)
def list_patient_caregivers(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[PatientCaregiverLinkRead]:
    links = CaregiverService(db).list_links_for_patient(patient.id)
    return [PatientCaregiverLinkRead.model_validate(l) for l in links]
