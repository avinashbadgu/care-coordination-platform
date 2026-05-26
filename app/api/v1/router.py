from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    care_plans,
    caregivers,
    documents,
    escalations,
    handoff,
    medications,
    patients,
    reminders,
    summaries,
    timeline,
    voice_notes,
)

api_router = APIRouter(prefix="/v1")
api_router.include_router(patients.router)
api_router.include_router(caregivers.router)
api_router.include_router(timeline.router)
api_router.include_router(medications.router)
api_router.include_router(reminders.router)
api_router.include_router(care_plans.router)
api_router.include_router(documents.router)
api_router.include_router(voice_notes.router)
api_router.include_router(alerts.router)
api_router.include_router(escalations.router)
api_router.include_router(summaries.router)
api_router.include_router(handoff.router)
