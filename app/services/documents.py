from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import (
    CONFIDENCE_REVIEW_THRESHOLD,
    AIProvider,
    get_ai_provider,
)
from app.core.event_types import EventType, Urgency
from app.core.storage import FileStorage, get_storage
from app.models.document import DocumentKind, DocumentStatus, UploadedDocument
from app.services.timeline import TimelineService


class DocumentService:
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
        kind: DocumentKind = DocumentKind.OTHER,
        uploaded_by_caregiver_id: int | None = None,
    ) -> UploadedDocument:
        storage_path = self.storage.save_bytes(
            patient_id=patient_id,
            kind=kind.value,
            filename=original_filename,
            data=data,
        )

        doc = UploadedDocument(
            patient_id=patient_id,
            uploaded_by_caregiver_id=uploaded_by_caregiver_id,
            kind=kind,
            original_filename=original_filename,
            mime_type=mime_type,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
        )
        self.db.add(doc)
        self.db.flush()

        self.timeline.record(
            patient_id=patient_id,
            event_type=EventType.DOCUMENT_UPLOADED,
            summary=f"Uploaded {kind.value}: {original_filename}",
            payload={"document_id": doc.id, "kind": kind.value},
            actor_caregiver_id=uploaded_by_caregiver_id,
            related_document_id=doc.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def process(self, *, document_id: int) -> UploadedDocument:
        """Run the OCR → extraction → review pipeline for an uploaded doc."""
        doc = self.db.get(UploadedDocument, document_id)
        if doc is None:
            raise ValueError(f"document {document_id} not found")

        doc.status = DocumentStatus.OCR_RUNNING
        self.db.flush()

        try:
            raw = self.storage.read_bytes(doc.storage_path)
            ocr = self.ai.ocr(image_bytes=raw, filename=doc.original_filename)
            extraction = self.ai.extract_medical_entities(ocr.raw_text)
        except Exception as exc:  # noqa: BLE001
            doc.status = DocumentStatus.OCR_FAILED
            self.db.flush()
            self.timeline.record(
                patient_id=doc.patient_id,
                event_type=EventType.DOCUMENT_OCR_FAILED,
                urgency=Urgency.MEDIUM,
                summary=f"OCR failed for {doc.original_filename}",
                payload={"document_id": doc.id, "error": str(exc)},
                related_document_id=doc.id,
                commit=False,
            )
            self.db.commit()
            self.db.refresh(doc)
            return doc

        # Combined confidence: weakest link of OCR and extraction.
        combined_conf = round(min(ocr.confidence, extraction.confidence), 2)

        doc.raw_text = ocr.raw_text
        doc.extracted_entities = asdict(extraction)
        doc.confidence = combined_conf
        doc.status = (
            DocumentStatus.REVIEW_REQUIRED
            if combined_conf < CONFIDENCE_REVIEW_THRESHOLD
            else DocumentStatus.OCR_COMPLETED
        )
        self.db.flush()

        # Single timeline event captures completion + confidence; the
        # workflow engine will create review alerts when confidence is low.
        self.timeline.record(
            patient_id=doc.patient_id,
            event_type=EventType.DOCUMENT_OCR_COMPLETED,
            summary=f"OCR completed for {doc.original_filename}",
            payload={
                "document_id": doc.id,
                "ocr_confidence": ocr.confidence,
                "extraction_confidence": extraction.confidence,
                "medications": extraction.medications,
                "follow_up_actions": extraction.follow_up_actions,
            },
            confidence=combined_conf,
            related_document_id=doc.id,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get(self, document_id: int) -> UploadedDocument | None:
        return self.db.get(UploadedDocument, document_id)

    def list_for_patient(self, patient_id: int) -> list[UploadedDocument]:
        stmt = (
            select(UploadedDocument)
            .where(UploadedDocument.patient_id == patient_id)
            .order_by(UploadedDocument.id.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
