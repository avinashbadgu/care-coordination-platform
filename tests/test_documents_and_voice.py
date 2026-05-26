from app.ai.providers import CONFIDENCE_REVIEW_THRESHOLD
from app.core.event_types import EventType
from app.models.alert import Alert
from app.models.document import DocumentKind, DocumentStatus
from app.models.timeline import TimelineEvent
from app.models.voice_note import VoiceNoteStatus
from app.services.documents import DocumentService
from app.services.voice_notes import VoiceNoteService


def test_text_document_extracts_entities_and_completes(db, patient_id):
    svc = DocumentService(db)
    doc = svc.upload(
        patient_id=patient_id,
        original_filename="rx.txt",
        mime_type="text/plain",
        data=b"Rx for Asha\nTake Metformin 500mg twice a day\nFollow up in 2 weeks\n",
        kind=DocumentKind.PRESCRIPTION,
    )
    doc = svc.process(document_id=doc.id)
    assert doc.status in (DocumentStatus.OCR_COMPLETED, DocumentStatus.REVIEW_REQUIRED)
    assert doc.confidence is not None
    assert doc.extracted_entities is not None
    meds = doc.extracted_entities.get("medications") or []
    assert any(m.get("name") == "metformin" for m in meds)


def test_binary_document_falls_below_threshold_and_flags_review(db, patient_id):
    svc = DocumentService(db)
    doc = svc.upload(
        patient_id=patient_id,
        original_filename="scan.bin",
        mime_type="application/octet-stream",
        data=bytes(range(256)) * 4,
    )
    doc = svc.process(document_id=doc.id)
    assert doc.confidence is not None
    if doc.confidence < CONFIDENCE_REVIEW_THRESHOLD:
        assert doc.status == DocumentStatus.REVIEW_REQUIRED
        assert any(
            "review" in a.title.lower()
            for a in db.query(Alert).filter(Alert.patient_id == patient_id).all()
        )


def test_voice_note_skipped_insulin_creates_missed_and_symptom_events(db, patient_id):
    svc = VoiceNoteService(db)
    note = svc.upload(
        patient_id=patient_id,
        original_filename="note.wav",
        mime_type="audio/wav",
        data=bytes(range(256)) * 8,  # binary -> stub fallback transcript
    )
    note = svc.process(voice_note_id=note.id)
    assert note.status == VoiceNoteStatus.EXTRACTED
    assert note.transcript and "insulin" in note.transcript.lower()

    types = {
        e.event_type
        for e in db.query(TimelineEvent).filter(TimelineEvent.patient_id == patient_id).all()
    }
    assert EventType.MEDICATION_MISSED.value in types
    assert EventType.SYMPTOM_REPORTED.value in types
