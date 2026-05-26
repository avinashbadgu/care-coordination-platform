"""Pluggable AI provider interface.

The platform isolates AI behind a small Protocol so:
- the system runs offline (deterministic local stub by default)
- real providers (Tesseract, Whisper, GPT, Claude) drop in without touching
  service or route code
- confidence is always surfaced — low-confidence outputs must be flagged for
  human review (never silently used)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol


# --- result types --------------------------------------------------------

@dataclass
class OCRResult:
    raw_text: str
    confidence: float
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionResult:
    transcript: str
    confidence: float
    duration_seconds: float | None
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Structured medical entities extracted from text.

    All fields are best-effort; downstream code must respect `confidence`
    and the `needs_review` signal it implies (see CONFIDENCE_REVIEW_THRESHOLD).
    """

    medications: list[dict[str, Any]] = field(default_factory=list)
    doctors: list[str] = field(default_factory=list)
    test_values: list[dict[str, Any]] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    follow_up_actions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    provider: str = "unknown"


@dataclass
class SummaryResult:
    headline: str
    body: str
    metrics: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = "v0"
    provider: str = "unknown"


CONFIDENCE_REVIEW_THRESHOLD: float = 0.6
"""Below this, downstream code MUST mark the artifact for human review."""


# --- provider interface --------------------------------------------------

class AIProvider(Protocol):
    name: str

    def ocr(self, *, image_bytes: bytes, filename: str) -> OCRResult: ...

    def transcribe(self, *, audio_bytes: bytes, filename: str) -> TranscriptionResult: ...

    def extract_medical_entities(self, text: str) -> ExtractionResult: ...

    def summarize_day(
        self,
        *,
        patient_name: str,
        summary_date: date,
        events: list[dict[str, Any]],
    ) -> SummaryResult: ...


# --- deterministic local stub -------------------------------------------

_MEDICATION_HINTS = [
    "metformin", "insulin", "atorvastatin", "amlodipine", "lisinopril",
    "aspirin", "paracetamol", "ibuprofen", "amoxicillin", "warfarin",
]
_SYMPTOM_HINTS = [
    "dizzy", "dizziness", "fatigue", "tired", "nausea", "vomiting",
    "headache", "fever", "shortness of breath", "chest pain", "weak",
]
_FOLLOW_UP_HINTS = [
    "follow up", "follow-up", "next visit", "call doctor", "schedule",
    "appointment", "review",
]
_DOSAGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s?(mg|mcg|ml|units?)", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b")


class StubAIProvider:
    """Deterministic, dependency-free fake.

    Useful for local dev, tests, and demos without API keys. Output is
    intentionally simple but realistic enough to exercise the full pipeline
    including confidence-gated review and follow-up detection.
    """

    name: str = "stub"

    def ocr(self, *, image_bytes: bytes, filename: str) -> OCRResult:
        # Pretend OCR: if it looks like text already, decode; otherwise echo
        # a deterministic placeholder so downstream extraction still has
        # something to chew on.
        try:
            raw_text = image_bytes.decode("utf-8")
            confidence = 0.92
        except UnicodeDecodeError:
            raw_text = (
                f"[stub-ocr] document {filename}\n"
                "Rx: Metformin 500mg twice a day\n"
                "Follow up in 2 weeks\n"
            )
            confidence = 0.55  # below review threshold → forces review path
        return OCRResult(
            raw_text=raw_text, confidence=confidence, provider=self.name,
            metadata={"bytes": len(image_bytes)},
        )

    def transcribe(self, *, audio_bytes: bytes, filename: str) -> TranscriptionResult:
        try:
            transcript = audio_bytes.decode("utf-8")
            confidence = 0.9
        except UnicodeDecodeError:
            transcript = (
                "[stub-transcription] mom skipped insulin today "
                "and felt dizzy after lunch follow up tomorrow"
            )
            confidence = 0.7
        return TranscriptionResult(
            transcript=transcript,
            confidence=confidence,
            duration_seconds=float(len(audio_bytes)) / 16000.0 if audio_bytes else None,
            provider=self.name,
        )

    def extract_medical_entities(self, text: str) -> ExtractionResult:
        lower = text.lower()
        meds: list[dict[str, Any]] = []
        for hint in _MEDICATION_HINTS:
            if hint in lower:
                # Try to pull a nearby dosage.
                window = lower.split(hint, 1)[1][:40] if hint in lower else ""
                m = _DOSAGE_RE.search(window)
                meds.append(
                    {
                        "name": hint,
                        "dosage": (m.group(0) if m else None),
                    }
                )
        symptoms = sorted({s for s in _SYMPTOM_HINTS if s in lower})
        follow_up = [phrase for phrase in _FOLLOW_UP_HINTS if phrase in lower]
        dates = sorted(set(_DATE_RE.findall(text)))

        # Confidence is a function of how much we actually pulled out.
        signal = len(meds) + len(symptoms) + len(follow_up)
        confidence = 0.4 + min(0.5, 0.1 * signal)

        return ExtractionResult(
            medications=meds,
            doctors=[],
            test_values=[],
            symptoms=symptoms,
            dates=dates,
            follow_up_actions=follow_up,
            confidence=round(confidence, 2),
            provider=self.name,
        )

    def summarize_day(
        self,
        *,
        patient_name: str,
        summary_date: date,
        events: list[dict[str, Any]],
    ) -> SummaryResult:
        counts: dict[str, int] = {}
        for ev in events:
            counts[ev.get("event_type", "unknown")] = (
                counts.get(ev.get("event_type", "unknown"), 0) + 1
            )

        taken = counts.get("medication_taken", 0)
        missed = counts.get("medication_missed", 0)
        scheduled = counts.get("medication_scheduled", 0)
        alerts = counts.get("alert_raised", 0)
        escalations = counts.get("escalation_triggered", 0)

        body_lines = [
            f"Daily summary for {patient_name} on {summary_date.isoformat()}.",
            f"- Medications taken: {taken}",
            f"- Medications missed: {missed}",
            f"- New medications scheduled: {scheduled}",
            f"- Alerts raised: {alerts}",
            f"- Escalations triggered: {escalations}",
        ]
        if missed:
            body_lines.append(
                "- Caregivers should review missed-dose details and confirm follow-up."
            )

        adherence = (
            taken / (taken + missed) if (taken + missed) else None
        )
        return SummaryResult(
            headline=(
                f"{taken} taken / {missed} missed, "
                f"{alerts} alerts, {escalations} escalations"
            ),
            body="\n".join(body_lines),
            metrics={
                "event_counts": counts,
                "adherence_ratio": adherence,
            },
            prompt_version="stub-v1",
            provider=self.name,
        )


_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider:
    """Return the process-wide AI provider.

    For MVP this is always the deterministic stub. Swap in production
    providers by setting this at app startup based on settings.
    """
    global _provider
    if _provider is None:
        _provider = StubAIProvider()
    return _provider


def set_ai_provider(provider: AIProvider) -> None:
    global _provider
    _provider = provider
