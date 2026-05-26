from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import AIProvider, get_ai_provider
from app.core.event_types import EventType, Urgency
from app.core.storage import FileStorage, get_storage
from app.models.voice_note import VoiceNote, VoiceNoteStatus
from app.services.timeline import TimelineService


def _detect_signals(transcript: str) -> dict[str, list[str]]:
    """Map low-level cues in a transcript to operational hints.

    Kept rule-based and tiny so the behaviour is deterministic. AI extraction
    is what fills in `medications` / `symptoms`; this function decides which
    operational events the voice note should produce.
    """
    lower = transcript.lower()
    missed_terms = ["skipped", "missed", "didn't take", "didnt take", "forgot"]
    symptom_terms = [
        "dizzy", "dizziness", "fatigue", "nausea", "vomiting",
        "headache", "fever", "chest pain", "shortness of breath",
    ]
    abnormal_terms = ["abnormal", "high bp", "low bp", "high sugar", "low sugar"]

    return {
        "medication_missed": [t for t in missed_terms if t in lower],
        "symptoms": [t for t in symptom_terms if t in lower],
        "abnormal": [t for t in abnormal_terms if t in lower],
    }


class VoiceNoteService:
    def __init__(
        self,
        db: Session,
        *,
        ai: AIProvider | None = None,
        storage: FileStorage | None = None,
    ) -> None:
        self.db = db
        self.ai = ai or get_ai_provider()
        self.storage = storage or get_storage()
        self.timeline = TimelineService(db)

    def upload(
        self,
        *,
        patient_id: int,
        original_filename: str,
        mime_type: str | None,
        data: bytes,
        recorded_by_caregiver_id: int | None = None,
    ) -> VoiceNote:
        storage_path = self.storage.save_bytes(
            patient_id=patient_id,
            kind="voice_notes",
            filename=original_filename,
            data=data,
        )
        note = VoiceNote(
            patient_id=patient_id,
            recorded_by_caregiver_id=recorded_by_caregiver_id,
            original_filename=original_filename,
            mime_type=mime_type,
            storage_path=storage_path,
            status=VoiceNoteStatus.UPLOADED,
        )
        self.db.add(note)
        self.db.flush()

        self.timeline.record(
            patient_id=patient_id,
            event_type=EventType.VOICE_NOTE_UPLOADED,
            summary=f"Voice note uploaded: {original_filename}",
            payload={"voice_note_id": note.id},
            actor_caregiver_id=recorded_by_caregiver_id,
            related_voice_note_id=note.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(note)
        return note

    def process(self, *, voice_note_id: int) -> VoiceNote:
        note = self.db.get(VoiceNote, voice_note_id)
        if note is None:
            raise ValueError(f"voice note {voice_note_id} not found")

        note.status = VoiceNoteStatus.TRANSCRIBING
        self.db.flush()

        try:
            raw = self.storage.read_bytes(note.storage_path)
            stt = self.ai.transcribe(audio_bytes=raw, filename=note.original_filename)
            extraction = self.ai.extract_medical_entities(stt.transcript)
        except Exception as exc:  # noqa: BLE001
            note.status = VoiceNoteStatus.FAILED
            self.db.flush()
            self.timeline.record(
                patient_id=note.patient_id,
                event_type=EventType.TRANSCRIPTION_FAILED,
                urgency=Urgency.MEDIUM,
                summary=f"Transcription failed for {note.original_filename}",
                payload={"voice_note_id": note.id, "error": str(exc)},
                related_voice_note_id=note.id,
                commit=False,
            )
            self.db.commit()
            self.db.refresh(note)
            return note

        note.transcript = stt.transcript
        note.duration_seconds = stt.duration_seconds
        note.extracted_entities = asdict(extraction)
        note.confidence = round(min(stt.confidence, extraction.confidence), 2)
        note.status = VoiceNoteStatus.EXTRACTED
        self.db.flush()

        self.timeline.record(
            patient_id=note.patient_id,
            event_type=EventType.TRANSCRIPTION_COMPLETED,
            summary=stt.transcript[:140] or f"Transcript for {note.original_filename}",
            payload={
                "voice_note_id": note.id,
                "transcript_confidence": stt.confidence,
                "extraction_confidence": extraction.confidence,
                "medications": extraction.medications,
                "symptoms": extraction.symptoms,
            },
            confidence=note.confidence,
            related_voice_note_id=note.id,
            commit=False,
        )

        # Map detected signals to operational events. These flow through the
        # workflow engine just like manually-entered events.
        signals = _detect_signals(stt.transcript)
        if signals["medication_missed"]:
            self.timeline.record(
                patient_id=note.patient_id,
                event_type=EventType.MEDICATION_MISSED,
                urgency=Urgency.MEDIUM,
                summary="Missed medication mentioned in voice note",
                payload={
                    "voice_note_id": note.id,
                    "trigger_terms": signals["medication_missed"],
                    "medication_name": (extraction.medications[0]["name"]
                                        if extraction.medications else None),
                },
                source="voice_note",
                related_voice_note_id=note.id,
                commit=False,
            )
        if signals["symptoms"] or extraction.symptoms:
            self.timeline.record(
                patient_id=note.patient_id,
                event_type=EventType.SYMPTOM_REPORTED,
                urgency=Urgency.MEDIUM,
                summary=f"Symptoms reported: {', '.join(extraction.symptoms or signals['symptoms'])}",
                payload={
                    "voice_note_id": note.id,
                    "symptoms": extraction.symptoms or signals["symptoms"],
                },
                source="voice_note",
                related_voice_note_id=note.id,
                commit=False,
            )
        if signals["abnormal"]:
            self.timeline.record(
                patient_id=note.patient_id,
                event_type=EventType.ABNORMAL_READING_DETECTED,
                urgency=Urgency.HIGH,
                summary=f"Abnormal reading mentioned: {', '.join(signals['abnormal'])}",
                payload={"voice_note_id": note.id, "terms": signals["abnormal"]},
                source="voice_note",
                related_voice_note_id=note.id,
                commit=False,
            )

        self.db.commit()
        self.db.refresh(note)
        return note

    def get(self, voice_note_id: int) -> VoiceNote | None:
        return self.db.get(VoiceNote, voice_note_id)

    def list_for_patient(self, patient_id: int) -> list[VoiceNote]:
        stmt = (
            select(VoiceNote)
            .where(VoiceNote.patient_id == patient_id)
            .order_by(VoiceNote.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
