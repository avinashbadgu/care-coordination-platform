from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_existing_patient
from app.models.patient import Patient
from app.schemas.voice_note import VoiceNoteRead
from app.services.voice_notes import VoiceNoteService

router = APIRouter(prefix="/patients/{patient_id}/voice-notes", tags=["voice-notes"])


@router.post("", response_model=VoiceNoteRead, status_code=status.HTTP_201_CREATED)
async def upload_voice_note(
    file: UploadFile = File(...),
    recorded_by_caregiver_id: int | None = Form(default=None),
    process_immediately: bool = Form(default=True),
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> VoiceNoteRead:
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="empty upload"
        )
    svc = VoiceNoteService(db)
    note = svc.upload(
        patient_id=patient.id,
        original_filename=file.filename or "voice-note",
        mime_type=file.content_type,
        data=data,
        recorded_by_caregiver_id=recorded_by_caregiver_id,
    )
    if process_immediately:
        note = svc.process(voice_note_id=note.id)
    return VoiceNoteRead.model_validate(note)


@router.post("/{voice_note_id}/process", response_model=VoiceNoteRead)
def reprocess_voice_note(
    voice_note_id: int,
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> VoiceNoteRead:
    svc = VoiceNoteService(db)
    note = svc.get(voice_note_id)
    if note is None or note.patient_id != patient.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="voice note not found")
    note = svc.process(voice_note_id=voice_note_id)
    return VoiceNoteRead.model_validate(note)


@router.get("", response_model=list[VoiceNoteRead])
def list_voice_notes(
    patient: Patient = Depends(get_existing_patient),
    db: Session = Depends(get_db),
) -> list[VoiceNoteRead]:
    items = VoiceNoteService(db).list_for_patient(patient.id)
    return [VoiceNoteRead.model_validate(v) for v in items]
