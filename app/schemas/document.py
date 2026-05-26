from datetime import datetime
from typing import Any

from app.models.document import DocumentKind, DocumentStatus
from app.schemas.common import ORMModel


class UploadedDocumentRead(ORMModel):
    id: int
    patient_id: int
    uploaded_by_caregiver_id: int | None
    kind: DocumentKind
    original_filename: str
    mime_type: str | None
    storage_path: str
    status: DocumentStatus
    raw_text: str | None
    extracted_entities: dict[str, Any] | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime
