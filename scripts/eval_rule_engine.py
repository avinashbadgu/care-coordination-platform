"""Evaluation harness for the deterministic escalation rule engine.

Each scenario is a self-contained sequence of timeline events with the
*expected* alerts and escalations the engine should produce. The harness
runs every scenario against an isolated in-memory database, records the
actual outputs, and writes a markdown report to docs/eval/rule_engine.md.

Run with:
    python scripts/eval_rule_engine.py
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Force per-run isolated SQLite + storage BEFORE the app imports.
_TMP = Path(tempfile.mkdtemp(prefix="eval_"))
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{(_TMP / 'eval.sqlite').as_posix()}"
os.environ["STORAGE_DIR"] = str(_TMP / "storage")

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core import db as db_module  # noqa: E402
from app.ai.providers import CONFIDENCE_REVIEW_THRESHOLD  # noqa: E402
from app.core.event_types import EventType, Urgency  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.alert import Alert  # noqa: E402
from app.models.escalation import Escalation  # noqa: E402
from app.models.patient import Patient  # noqa: E402
from app.services.timeline import TimelineService  # noqa: E402


def _new_session():
    engine = create_engine(
        get_settings().resolved_database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return db_module.SessionLocal()


@dataclass
class TimelineInput:
    event_type: EventType
    urgency: Urgency = Urgency.LOW
    summary: str | None = None
    payload: dict | None = None
    confidence: float | None = None


@dataclass
class Expected:
    alerts: int = 0
    escalations: int = 0
    high_alerts: int = 0
    rule_names: list[str] = field(default_factory=list)


@dataclass
class Scenario:
    name: str
    description: str
    inputs: list[TimelineInput]
    expected: Expected


SCENARIOS: list[Scenario] = [
    Scenario(
        name="single_missed_dose",
        description="A single missed-dose event must raise exactly one medium alert.",
        inputs=[
            TimelineInput(
                event_type=EventType.MEDICATION_MISSED,
                urgency=Urgency.MEDIUM,
                payload={"medication_name": "Metformin"},
            )
        ],
        expected=Expected(alerts=1, escalations=0),
    ),
    Scenario(
        name="two_misses_in_24h",
        description="Two missed-dose events within 24h trigger a HIGH alert + escalation.",
        inputs=[
            TimelineInput(
                event_type=EventType.MEDICATION_MISSED,
                urgency=Urgency.MEDIUM,
                payload={"medication_name": "Insulin"},
            ),
            TimelineInput(
                event_type=EventType.MEDICATION_MISSED,
                urgency=Urgency.MEDIUM,
                payload={"medication_name": "Insulin"},
            ),
        ],
        expected=Expected(
            alerts=2, escalations=1, high_alerts=1,
            rule_names=["medication_missed_twice_in_24h"],
        ),
    ),
    Scenario(
        name="abnormal_reading_high",
        description="High-urgency abnormal reading must raise a HIGH alert.",
        inputs=[
            TimelineInput(
                event_type=EventType.ABNORMAL_READING_DETECTED,
                urgency=Urgency.HIGH,
                summary="Glucose 320 mg/dL",
                payload={"detail": "glucose=320"},
            )
        ],
        expected=Expected(alerts=1, high_alerts=1),
    ),
    Scenario(
        name="low_confidence_ocr",
        description=(
            "OCR completion below the review threshold must produce a review alert "
            "and a document_review_required event."
        ),
        inputs=[
            TimelineInput(
                event_type=EventType.DOCUMENT_OCR_COMPLETED,
                summary="OCR completed",
                confidence=CONFIDENCE_REVIEW_THRESHOLD - 0.1,
            )
        ],
        expected=Expected(alerts=1),
    ),
    Scenario(
        name="high_confidence_ocr",
        description=(
            "OCR completion above the review threshold must NOT raise any alerts."
        ),
        inputs=[
            TimelineInput(
                event_type=EventType.DOCUMENT_OCR_COMPLETED,
                summary="OCR completed",
                confidence=CONFIDENCE_REVIEW_THRESHOLD + 0.3,
            )
        ],
        expected=Expected(alerts=0),
    ),
    Scenario(
        name="symptom_reported",
        description="A symptom event must raise a medium-urgency alert.",
        inputs=[
            TimelineInput(
                event_type=EventType.SYMPTOM_REPORTED,
                summary="Patient reports dizziness",
                payload={"symptoms": ["dizziness"]},
            )
        ],
        expected=Expected(alerts=1),
    ),
]


@dataclass
class Result:
    scenario: Scenario
    actual_alerts: int
    actual_escalations: int
    actual_high_alerts: int
    actual_rules: list[str]

    @property
    def passed(self) -> bool:
        e = self.scenario.expected
        if self.actual_alerts != e.alerts:
            return False
        if self.actual_escalations != e.escalations:
            return False
        if self.actual_high_alerts != e.high_alerts:
            return False
        if e.rule_names and sorted(self.actual_rules) != sorted(e.rule_names):
            return False
        return True


def run(scenario: Scenario) -> Result:
    with _new_session() as db:
        patient = Patient(full_name=f"eval-{scenario.name}", timezone="UTC")
        db.add(patient)
        db.commit()
        db.refresh(patient)

        tl = TimelineService(db)
        for inp in scenario.inputs:
            tl.record(
                patient_id=patient.id,
                event_type=inp.event_type,
                urgency=inp.urgency,
                summary=inp.summary,
                payload=inp.payload,
                confidence=inp.confidence,
            )

        alerts = db.query(Alert).all()
        escalations = db.query(Escalation).all()
        return Result(
            scenario=scenario,
            actual_alerts=len(alerts),
            actual_escalations=len(escalations),
            actual_high_alerts=sum(1 for a in alerts if a.urgency == Urgency.HIGH),
            actual_rules=[e.rule for e in escalations if e.rule],
        )


def write_report(results: list[Result], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    passed = sum(r.passed for r in results)
    lines.append("# Rule engine evaluation\n")
    lines.append(
        f"Ran {len(results)} scenarios — **{passed}/{len(results)} passed**.\n"
    )
    lines.append("Generated by `scripts/eval_rule_engine.py`.\n\n")

    lines.append("| Scenario | Expected (A / E / H / rules) | Actual | Result |")
    lines.append("|---|---|---|---|")
    for r in results:
        e = r.scenario.expected
        exp = f"{e.alerts} / {e.escalations} / {e.high_alerts} / {','.join(e.rule_names) or '-'}"
        act = (
            f"{r.actual_alerts} / {r.actual_escalations} / {r.actual_high_alerts}"
            f" / {','.join(r.actual_rules) or '-'}"
        )
        verdict = "PASS" if r.passed else "FAIL"
        lines.append(f"| `{r.scenario.name}` | {exp} | {act} | **{verdict}** |")
    lines.append("")
    lines.append("Columns: **A**=alerts, **E**=escalations, **H**=high-urgency alerts.")
    lines.append("")

    lines.append("## Scenario details\n")
    for r in results:
        lines.append(f"### `{r.scenario.name}` — {('PASS' if r.passed else 'FAIL')}\n")
        lines.append(r.scenario.description)
        lines.append("")
        lines.append("Inputs:")
        for inp in r.scenario.inputs:
            extras = []
            if inp.urgency != Urgency.LOW:
                extras.append(f"urgency={inp.urgency.value}")
            if inp.confidence is not None:
                extras.append(f"confidence={inp.confidence:.2f}")
            if inp.payload:
                extras.append(f"payload={inp.payload}")
            extra = (" — " + ", ".join(extras)) if extras else ""
            lines.append(f"- `{inp.event_type.value}`{extra}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    results = [run(s) for s in SCENARIOS]
    out = Path("docs/eval/rule_engine.md")
    write_report(results, out)

    passed = sum(r.passed for r in results)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.scenario.name}")
    print(f"\nWrote {out}  ({passed}/{len(results)} passed)")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
