"""End-to-end smoke test across all eight MVP pillars.

Walks the platform like a real caregiver would:
  1. create a patient
  2. add a caregiver and link them
  3. create a care plan with tasks; complete one task
  4. schedule a medication; expand reminders for today; dispatch + ack
  5. force a miss to drive the escalation rule
  6. upload a document; observe OCR/extraction + low-confidence review path
  7. upload a voice note that mentions missed insulin + dizziness
  8. generate a daily summary
  9. read back timeline, alerts, escalations, summaries
"""
from __future__ import annotations

import io
import json
import os
from datetime import date, datetime, time, timezone
from pathlib import Path

# Use an isolated DB so repeated smoke runs don't accumulate state.
SMOKE_DB = Path("./care.smoke.sqlite").resolve()
SMOKE_DB.unlink(missing_ok=True)
SMOKE_STORAGE = Path("./storage.smoke").resolve()
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{SMOKE_DB.as_posix()}"
os.environ["STORAGE_DIR"] = str(SMOKE_STORAGE)

# Important: clear any cached settings/engine that previous imports may have
# captured before we set the env vars above.
from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.db import engine  # noqa: E402
from app.models import Base  # noqa: E402

Base.metadata.create_all(bind=engine)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def step(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    client = TestClient(app)

    step("health")
    r = client.get("/healthz")
    assert r.status_code == 200, r.text
    print(r.json())

    step("create patient")
    r = client.post(
        "/v1/patients",
        json={"full_name": "Asha Devi", "timezone": "Asia/Kolkata"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    print(f"patient id={pid}")

    step("create + link caregiver")
    r = client.post(
        "/v1/caregivers",
        json={"full_name": "Rohan (son)", "phone": "+91999"},
    )
    assert r.status_code == 201, r.text
    cgid = r.json()["id"]

    r = client.post(
        f"/v1/patients/{pid}/caregivers",
        json={"caregiver_id": cgid, "role": "family"},
    )
    assert r.status_code == 201, r.text
    print(f"linked caregiver id={cgid} role=family")

    step("create care plan with tasks; complete one")
    r = client.post(
        f"/v1/patients/{pid}/care-plans",
        json={
            "title": "Diabetes management",
            "description": "Daily routines",
            "created_by_caregiver_id": cgid,
            "tasks": [
                {"title": "Morning blood-sugar check", "cadence": "daily"},
                {"title": "30-min walk", "cadence": "daily"},
            ],
        },
    )
    assert r.status_code == 201, r.text
    plan = r.json()
    print(f"plan id={plan['id']} tasks={[t['title'] for t in plan['tasks']]}")

    first_task_id = plan["tasks"][0]["id"]
    r = client.post(
        f"/v1/care-plans/{plan['id']}/tasks/{first_task_id}/complete",
        json={"completed_by_caregiver_id": cgid, "notes": "98 mg/dL"},
    )
    assert r.status_code == 200, r.text
    print(f"task {first_task_id} completed")

    step("schedule medication; expand today's reminders; dispatch; ack")
    # Use times in the recent past so dispatch picks them up immediately.
    now_local = datetime.now()
    earlier_today = (now_local.replace(minute=0, second=0, microsecond=0)).strftime("%H:%M")
    r = client.post(
        f"/v1/patients/{pid}/medications",
        json={
            "medication_name": "Metformin",
            "dosage": "500mg",
            "times_of_day": [earlier_today, "23:50"],
        },
    )
    assert r.status_code == 201, r.text
    print(f"medication id={r.json()['id']} times={r.json()['times_of_day']}")

    r = client.post(f"/v1/patients/{pid}/reminders/expand")
    assert r.status_code == 200, r.text
    expanded = r.json()
    print(f"expanded {len(expanded)} reminders")

    r = client.post("/v1/reminders/dispatch")
    assert r.status_code == 200, r.text
    print(f"dispatched: {r.json()}")

    r = client.get(f"/v1/patients/{pid}/reminders")
    assert r.status_code == 200, r.text
    reminders = r.json()
    sent = next((rem for rem in reminders if rem["status"] == "sent"), None)
    assert sent, "expected at least one SENT reminder after dispatch"

    r = client.post(
        f"/v1/reminders/{sent['id']}/ack",
        json={"acknowledged_by_caregiver_id": cgid, "notes": "Taken with breakfast"},
    )
    assert r.status_code == 200, r.text
    print(f"acked reminder {sent['id']}")

    step("manually record a missed dose to drive escalation")
    client.post(
        f"/v1/patients/{pid}/timeline",
        json={
            "event_type": "medication_missed",
            "urgency": "medium",
            "summary": "Missed insulin at 13:00",
            "payload": {"medication_name": "Insulin"},
        },
    )
    client.post(
        f"/v1/patients/{pid}/timeline",
        json={
            "event_type": "medication_missed",
            "urgency": "medium",
            "summary": "Missed insulin at 19:00",
            "payload": {"medication_name": "Insulin"},
        },
    )
    r = client.get(f"/v1/patients/{pid}/escalations")
    assert r.status_code == 200, r.text
    escalations = r.json()
    print(f"escalations after second miss: {[e['rule'] for e in escalations]}")
    assert any(e["rule"] == "medication_missed_twice_in_24h" for e in escalations), (
        "expected escalation rule to fire on second miss"
    )

    step("upload + process a text 'document' (prescription)")
    doc_bytes = (
        b"Rx for Asha Devi\n"
        b"Take Metformin 500mg twice a day\n"
        b"Follow up in 2 weeks\n"
    )
    files = {"file": ("rx.txt", io.BytesIO(doc_bytes), "text/plain")}
    r = client.post(
        f"/v1/patients/{pid}/documents",
        files=files,
        data={"kind": "prescription"},
    )
    assert r.status_code == 201, r.text
    doc = r.json()
    print(f"document id={doc['id']} status={doc['status']} conf={doc['confidence']}")
    assert doc["extracted_entities"], "expected extraction payload"

    step("upload + process a binary 'voice note' (forces stub transcript)")
    # Random-ish bytes that won't decode as utf-8 → forces the stub's
    # deterministic fallback transcript that mentions missed insulin + dizziness.
    audio = bytes(range(256)) * 8
    files = {"file": ("note.wav", io.BytesIO(audio), "audio/wav")}
    r = client.post(
        f"/v1/patients/{pid}/voice-notes",
        files=files,
        data={"recorded_by_caregiver_id": str(cgid)},
    )
    assert r.status_code == 201, r.text
    note = r.json()
    print(f"voice note id={note['id']} status={note['status']} conf={note['confidence']}")
    assert note["transcript"], "expected a transcript"

    step("alerts after voice note")
    r = client.get(f"/v1/patients/{pid}/alerts")
    assert r.status_code == 200, r.text
    alerts = r.json()
    print(f"total alerts: {len(alerts)}")
    for a in alerts[:6]:
        print(f"  - [{a['urgency']}] {a['title']}")

    step("generate daily summary")
    r = client.post(f"/v1/patients/{pid}/summaries")
    assert r.status_code == 201, r.text
    summary = r.json()
    print(f"headline: {summary['headline']}")
    print(summary["body"])
    print(f"metrics: {json.dumps(summary['metrics'], indent=2)}")

    step("final timeline (most recent 25)")
    r = client.get(f"/v1/patients/{pid}/timeline", params={"limit": 25})
    assert r.status_code == 200, r.text
    page = r.json()
    print(f"timeline events total={page['total']}")
    for ev in page["items"]:
        print(f"  - {ev['occurred_at']}  {ev['urgency']:<6} {ev['event_type']:<28} {ev['summary'] or ''}")

    print("\nSMOKE OK")


if __name__ == "__main__":
    main()
