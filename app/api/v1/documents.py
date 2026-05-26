from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.document import DocumentKind
from app.models.patient import Patient
from app.schemas.document import UploadedDocumentRead
from app.services.documents import DocumentService

router = APIRouter(prefix="/patients/{patient_id}/documents", tags=["documents"])


@router.post("", response_model=UploadedDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    kind: DocumentKind = Form(DocumentKind.OTHER),
    uploaded_by_caregiver_id: int | None = Form(default=None),
    process_immediately: bool = Form(default=True),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="empty upload"
        )
    svc = DocumentService(db)
    doc = svc.upload(
        patient_id=patient.id,
        original_filename=file.filename or "upload",
        mime_type=file.content_type,
        data=data,
        kind=kind,
        uploaded_by_caregiver_id=uploaded_by_caregiver_id,
    )
    if process_immediately:
        doc = svc.process(document_id=doc.id)
    return UploadedDocumentRead.model_validate(doc)


@router.post(
    "/{document_id}/process",
    response_model=UploadedDocumentRead,
)
def reprocess_document(
    document_id: int,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> UploadedDocumentRead:
    svc = DocumentService(db)
    doc = svc.get(document_id)
    if doc is None or doc.patient_id != patient.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
    doc = svc.process(document_id=document_id)
    return UploadedDocumentRead.model_validate(doc)


@router.get("", response_model=list[UploadedDocumentRead])
def list_documents(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[UploadedDocumentRead]:
    items = DocumentService(db).list_for_patient(patient.id)
    return [UploadedDocumentRead.model_validate(d) for d in items]
