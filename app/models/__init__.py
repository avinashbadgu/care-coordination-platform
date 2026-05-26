"""SQLAlchemy ORM models. Import all modules so Alembic autogenerate sees them."""

from app.models.base import Base
from app.models.patient import Patient
from app.models.caregiver import Caregiver, PatientCaregiver
from app.models.care_plan import CarePlan, CarePlanTask
from app.models.timeline import TimelineEvent
from app.models.medication import MedicationSchedule
from app.models.reminder import Reminder
from app.models.document import UploadedDocument
from app.models.voice_note import VoiceNote
from app.models.alert import Alert
from app.models.escalation import Escalation
from app.models.summary import DailySummary

__all__ = [
    "Base",
    "Patient",
    "Caregiver",
    "PatientCaregiver",
    "CarePlan",
    "CarePlanTask",
    "TimelineEvent",
    "MedicationSchedule",
    "Reminder",
    "UploadedDocument",
    "VoiceNote",
    "Alert",
    "Escalation",
    "DailySummary",
]
