from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.escalation import EscalationRead
from app.services.escalations import EscalationService

router = APIRouter(tags=["escalations"])


@router.get("/patients/{patient_id}/escalations", response_model=list[EscalationRead])
def list_escalations(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[EscalationRead]:
    items = EscalationService(db).list_for_patient(patient.id)
    return [EscalationRead.model_validate(e) for e in items]


@router.post("/escalations/{escalation_id}/resolve", response_model=EscalationRead)
def resolve_escalation(escalation_id: int, db: Session = Depends(get_db)) -> EscalationRead:
    escalation = EscalationService(db).resolve(escalation_id=escalation_id)
    if escalation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="escalation not found")
    return EscalationRead.model_validate(escalation)
