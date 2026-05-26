from enum import StrEnum


class EventType(StrEnum):
    """Canonical operational event taxonomy.

    Timeline is the source of truth — every meaningful action becomes a typed
    event. Add new types here; do not invent ad-hoc strings at call sites.
    """

    # Medication
    MEDICATION_SCHEDULED = "medication_scheduled"
    MEDICATION_TAKEN = "medication_taken"
    MEDICATION_MISSED = "medication_missed"
    MEDICATION_SKIPPED = "medication_skipped"

    # Reminders
    REMINDER_SENT = "reminder_sent"
    REMINDER_ACKNOWLEDGED = "reminder_acknowledged"
    REMINDER_FAILED = "reminder_failed"

    # Documents
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_OCR_COMPLETED = "document_ocr_completed"
    DOCUMENT_OCR_FAILED = "document_ocr_failed"
    DOCUMENT_REVIEW_REQUIRED = "document_review_required"

    # Voice
    VOICE_NOTE_UPLOADED = "voice_note_uploaded"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_FAILED = "transcription_failed"

    # Care plan
    CARE_PLAN_CREATED = "care_plan_created"
    CARE_PLAN_UPDATED = "care_plan_updated"
    CARE_PLAN_TASK_COMPLETED = "care_plan_task_completed"

    # Observations
    ABNORMAL_READING_DETECTED = "abnormal_reading_detected"
    SYMPTOM_REPORTED = "symptom_reported"

    # Alerts / escalation
    ALERT_RAISED = "alert_raised"
    ALERT_RESOLVED = "alert_resolved"
    ESCALATION_TRIGGERED = "escalation_triggered"
    ESCALATION_RESOLVED = "escalation_resolved"
    CAREGIVER_NOTIFIED = "caregiver_notified"

    # Appointments
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_REMINDED = "appointment_reminded"

    # Summaries
    DAILY_SUMMARY_GENERATED = "daily_summary_generated"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CaregiverRole(StrEnum):
    PATIENT = "patient"
    FAMILY = "family"
    CARETAKER = "caretaker"
    NURSE = "nurse"
    ADMIN = "admin"
