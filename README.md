# AI Care Coordination & Workflow Intelligence Platform

An operational care-coordination platform for patients, family caregivers,
nurses, and caretakers. The product is **workflows** — timelines, reminders,
adherence tracking, escalations, shift handoffs, daily summaries, and
multimodal AI intelligence over documents and voice notes.

> AI is a supporting layer. **Workflows are the core product.**

This is **not** an AI doctor, diagnosis engine, symptom checker, telemedicine
app, or generic healthcare chatbot. The full design constitution lives in
[CLAUDE.md](CLAUDE.md).

---

## Proof artifacts at a glance

| What | Result | Where |
|---|---|---|
| Backend pytest suite | **24 passed in 9.75s** | [`tests/`](tests/) |
| Test coverage (`app/`) | **84%** (line) | regenerate via `pytest --cov=app` |
| Rule-engine evaluation | **6/6 scenarios PASS** | [`docs/eval/rule_engine.md`](docs/eval/rule_engine.md) |
| Documented failure case | low-confidence OCR is gated, not trusted | [`docs/failures/low_confidence_ocr.md`](docs/failures/low_confidence_ocr.md) |
| Demo dataset | 3 patients with realistic multi-day history | `python scripts/load_demo_data.py` |
| End-to-end smoke | runs every pillar in under a second | `python scripts/smoke_test.py` |
| Frontend build | **11 routes**, TypeScript strict, `next build` clean | `cd frontend && npm run build` |

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Architecture](#architecture)
- [The eight MVP pillars + handoff](#the-eight-mvp-pillars--handoff)
- [Tech stack](#tech-stack)
- [Quickstart](#quickstart)
- [Demo data](#demo-data)
- [Screenshots](#screenshots)
- [Project layout](#project-layout)
- [Event taxonomy](#event-taxonomy)
- [Escalation rules engine](#escalation-rules-engine)
- [Evaluation & failure cases](#evaluation--failure-cases)
- [Tests & coverage](#tests--coverage)
- [AI providers (pluggable)](#ai-providers-pluggable)
- [Workers & operations](#workers--operations)
- [Non-goals](#non-goals)

---

## Why this exists

Caregiving for older or chronically ill patients fragments fast:
- WhatsApp threads instead of structured handoffs
- Prescriptions photographed and forgotten in a phone gallery
- Voice notes nobody re-listens to
- Missed medications nobody escalates on
- No single source of truth for what's actually happening day to day

This platform turns that chaos into a typed, auditable timeline of operational
events — and uses AI **only** to summarize, extract, classify, and
prioritize, never to diagnose or recommend treatment.

---

## Architecture

```
                    AI Care Coordination Platform
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
   Workflow Engine         AI Processing Layer        Timeline Engine
   reminders / escalations OCR / STT / extraction     event history / search
        |                         |                         |
        v                         v                         v
   Notification Layer      Risk Prioritization        Analytics / Summaries
                                  |
                                  v
                        Observability + Audit Logs
```

**The Timeline is the source of truth.** Every meaningful action — a
reminder being sent, a document being OCR'd, a missed dose detected, an
escalation triggered — flows through `TimelineService.record()` and becomes a
typed `TimelineEvent`. The deterministic workflow engine is wired into that
chokepoint, so escalations are driven by data, not by ad-hoc service calls.

---

## The eight MVP pillars + handoff

| # | Pillar                       | Endpoints (prefix `/v1`)                                                                 |
|---|------------------------------|------------------------------------------------------------------------------------------|
| 1 | Unified care timeline        | `GET/POST /patients/{id}/timeline`  (filters: type, urgency, actor, source, since/until) |
| 2 | Medication workflow          | `/patients/{id}/medications`, `/patients/{id}/reminders`, `/reminders/{id}/ack`, `/reminders/dispatch`, `/reminders/detect-misses` |
| 3 | Care plan management         | `/patients/{id}/care-plans`, `/care-plans/{id}/tasks/{tid}/complete`                     |
| 4 | Document intelligence        | `/patients/{id}/documents` (upload + OCR + extraction + confidence-gated review)         |
| 5 | Voice note intelligence      | `/patients/{id}/voice-notes` (upload + transcription + extraction + signal detection)    |
| 6 | Smart escalation             | Deterministic rule engine hooked into `TimelineService`; `/patients/{id}/escalations`    |
| 7 | Multi-caregiver coordination | `/caregivers`, `/patients/{id}/caregivers` (with roles)                                  |
| 8 | Daily AI summaries           | `/patients/{id}/summaries`                                                               |
| + | **Shift handoff summaries**  | `/patients/{id}/handoff?hours=12` — night → morning caregiver operational digest         |

Every pillar has a corresponding page in the Next.js frontend.

---

## Tech stack

**Backend**
- FastAPI + Uvicorn
- SQLAlchemy 2 + Alembic (SQLite for local development, PostgreSQL for production)
- Pydantic v2 for boundary validation
- Pluggable AI provider Protocol with a deterministic local stub by default

**Frontend**
- Next.js 15 (App Router, React 19, server components)
- Tailwind CSS v3 with shadcn-style design tokens, in-tree components
- Radix UI primitives (Dialog, Tabs, Label, Separator)
- Typed API client mirroring backend schemas

**Infrastructure choices.** Single-node architecture: one FastAPI app, one
relational database, CLI worker entry points. No Celery / Redis / Kubernetes
in the MVP. The platform is designed so async fan-out can be added later
without rework, not as upfront tax.

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+
- Windows users: `tzdata` is pulled in via the wheel; on Linux / macOS the
  system tz database is used.

### Backend

```bash
# from project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1               # Windows PowerShell
# source .venv/bin/activate                # macOS / Linux

pip install -e ".[dev]"
python scripts/create_dev_db.py            # creates ./care.sqlite from metadata
python scripts/load_demo_data.py           # optional: populate three demo patients
uvicorn app.main:app --reload              # http://localhost:8000  -- OpenAPI at /docs
```

For PostgreSQL, set `DATABASE_URL` in `.env` (copy from `.env.example`) and
run Alembic instead of `create_dev_db.py`:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
npm run dev                                # http://localhost:3000
```

The dev server reads the API base from `NEXT_PUBLIC_API_BASE`
(default `http://localhost:8000`).

---

## Demo data

```bash
python scripts/load_demo_data.py
```

Creates three patients with progressively richer history so the dashboard
has something meaningful to display:

1. **Asha Devi (demo)** — diabetic, two days of timeline including a
   `medication_missed_twice_in_24h` escalation, an extracted prescription,
   a voice note that produced a `symptom_reported` event, and a generated
   daily summary.
2. **Ravi Kumar (demo)** — elderly, three medication schedules, today's
   reminders expanded and mostly acknowledged.
3. **Lin Wei (demo)** — newly added with a single medication; exists to
   exercise the empty-state UX in the frontend.

Re-running the script is idempotent — it deletes the demo patients first,
then reloads them.

---

## Screenshots

Screenshots live in [`docs/screenshots/`](docs/screenshots/). The directory
is empty by default; capture your own with the stack running:

```bash
# terminal 1
uvicorn app.main:app --reload
# terminal 2
cd frontend && npm run dev
# then open http://localhost:3000/patients/2 and capture
```

Suggested captures:

| Filename | Page | What to show |
|---|---|---|
| `timeline.png` | `/patients/2` | Stat cards + the typed event feed for the demo diabetic patient |
| `reminders.png` | `/patients/2/reminders` | Expanded reminders with Sent / Acknowledged / Missed states + Ack action |
| `documents.png` | `/patients/2/documents` | Uploaded prescription with `confidence` column and status |
| `voice-notes.png` | `/patients/2/voice-notes` | Transcript card with extracted entities expanded |
| `alerts.png` | `/patients/2/alerts` | Open high-urgency alert + escalation, with Resolve buttons |
| `handoff.png` | `/patients/2/handoff?hours=24` | Shift handoff card with adherence + open incidents |
| `summary.png` | `/patients/2/summaries` | Generated daily summary body + metrics |

Reference them in the README as `![timeline](docs/screenshots/timeline.png)`.

---

## Project layout

```
.
├── app/
│   ├── core/                 config, db, logging, storage, event_types
│   ├── ai/                   AIProvider Protocol + deterministic StubAIProvider
│   ├── models/               11 SQLAlchemy 2 models
│   ├── schemas/              Pydantic boundary schemas
│   ├── services/             timeline, patients, caregivers, medications,
│   │                         reminders, care_plans, documents, voice_notes,
│   │                         alerts, escalations, summaries, handoff,
│   │                         notifications
│   ├── workflows/            deterministic rule engine
│   ├── api/v1/               thin routers (42 routes)
│   ├── workers/              CLI: reminders, summaries (cron-friendly)
│   └── main.py               FastAPI app + CORS + /healthz
├── alembic/                  migrations
├── frontend/                 Next.js 15 app
│   ├── app/                  pages (server components by default)
│   ├── components/           UI primitives (shadcn-style, in-tree)
│   └── lib/                  typed API client + types + utils
├── tests/                    pytest suite (24 tests, 84% coverage)
├── scripts/                  create_dev_db, load_demo_data, smoke_test,
│                             eval_rule_engine
├── docs/
│   ├── eval/rule_engine.md   generated evaluation report
│   ├── failures/             documented failure cases
│   └── screenshots/          (your captures)
├── CLAUDE.md                 project constitution (workflows, not chat)
└── pyproject.toml
```

---

## Event taxonomy

Add new event types in [app/core/event_types.py](app/core/event_types.py) —
never invent ad-hoc strings at call sites.

Current taxonomy:

```
medication_scheduled, medication_taken, medication_missed, medication_skipped
reminder_sent, reminder_acknowledged, reminder_failed
document_uploaded, document_ocr_completed, document_ocr_failed, document_review_required
voice_note_uploaded, transcription_completed, transcription_failed
care_plan_created, care_plan_updated, care_plan_task_completed
abnormal_reading_detected, symptom_reported
alert_raised, alert_resolved
escalation_triggered, escalation_resolved, caregiver_notified
appointment_created, appointment_reminded
daily_summary_generated
```

Each event carries `urgency` (low/medium/high), an optional `payload` JSON
blob, attribution (`source`, `actor_caregiver_id`), AI `confidence`, and
optional reverse-links to the originating row (`related_medication_id`,
`related_reminder_id`, `related_document_id`, `related_voice_note_id`).

The timeline list endpoint supports filtering by event type, urgency, actor
caregiver, source, and time window — enough to drive event-replay style UI
without changing the data model.

---

## Escalation rules engine

Deterministic, auditable, hooked into `TimelineService.record()`. AI never
controls critical alerting logic.

| Rule | Trigger | Effect |
|------|---------|--------|
| Missed medication, single | `medication_missed` event | medium-urgency alert |
| Missed medication, repeated | 2+ `medication_missed` in 24h | **high-urgency alert + escalation** |
| Abnormal reading | `abnormal_reading_detected` event | alert at reported urgency |
| Low-confidence document | `document_ocr_completed` with `confidence < 0.6` | `document_review_required` event + medium alert |
| Symptom reported | `symptom_reported` event | medium-urgency alert |

New rules live in [app/workflows/engine.py](app/workflows/engine.py). They
are plain functions of `(db, triggering_event) -> None` that create alerts
or escalations via their respective services with `commit=False` to join
the outer transaction.

---

## Evaluation & failure cases

The rule engine has a runnable evaluation harness:

```bash
python scripts/eval_rule_engine.py
```

Sample output (committed in [`docs/eval/rule_engine.md`](docs/eval/rule_engine.md)):

```
  [PASS] single_missed_dose
  [PASS] two_misses_in_24h
  [PASS] abnormal_reading_high
  [PASS] low_confidence_ocr
  [PASS] high_confidence_ocr
  [PASS] symptom_reported

Wrote docs/eval/rule_engine.md  (6/6 passed)
```

Each scenario declares the expected alert count, escalation count,
high-urgency alert count, and rule names. The harness exercises the actual
`TimelineService` + `WorkflowEngine` against an isolated in-memory database
and diffs the results. Add new scenarios by appending to `SCENARIOS` in
[`scripts/eval_rule_engine.py`](scripts/eval_rule_engine.py); the markdown
report regenerates on every run.

**Documented failure case:** how the platform handles a low-confidence OCR
output without silently trusting it →
[`docs/failures/low_confidence_ocr.md`](docs/failures/low_confidence_ocr.md).

---

## Tests & coverage

```bash
.\.venv\Scripts\python.exe -m pytest tests/ --cov=app -q
```

Latest run:

```
24 passed, 1 warning in 9.75s
TOTAL  1812 stmts  285 miss  84% cover
```

Coverage is concentrated on the business-critical paths called out in
CLAUDE.md:

| Module | Coverage |
|---|---|
| `app/services/timeline.py` | 88% |
| `app/services/reminders.py` | 91% |
| `app/services/medications.py` | 91% |
| `app/services/summaries.py` | 93% |
| `app/services/handoff.py` | 94% |
| `app/workflows/engine.py` | **95%** |
| `app/ai/providers.py` | 98% |
| Pydantic schemas (boundary validation) | 100% |
| ORM models | 100% |

The two `app/workers/*.py` modules at 0% are CLI argparse wrappers around
the already-covered services; they are exercised manually via cron-style
runs, not in unit tests.

---

## AI providers (pluggable)

The platform isolates AI behind a small Protocol so:

- The system runs **offline by default** — a deterministic `StubAIProvider`
  ships with the project and is used unless you swap it.
- Real providers (Tesseract, Whisper, GPT, Claude, Azure Cognitive Services)
  drop in without touching service or route code.
- Confidence is surfaced on every output — low-confidence results are
  automatically flagged for human review (see [the failure case](docs/failures/low_confidence_ocr.md)).

To plug in a real provider, implement the `AIProvider` Protocol in
[app/ai/providers.py](app/ai/providers.py) and register it at startup:

```python
from app.ai.providers import set_ai_provider

set_ai_provider(MyOpenAIProvider(api_key=...))
```

The `CONFIDENCE_REVIEW_THRESHOLD` constant (default `0.6`) controls when
downstream code marks an artifact for review.

---

## Workers & operations

Two cron-friendly CLI workers ship with the project:

```bash
# Expand today's reminders, dispatch due ones, detect missed doses
python -m app.workers.reminders --all
python -m app.workers.reminders --patient 1

# Generate daily summaries
python -m app.workers.summaries --all
python -m app.workers.summaries --patient 1 --date 2026-05-25
```

Schedule them with `cron` on Linux / macOS or Task Scheduler on Windows.
Promote to Celery / ARQ if you need async fan-out — the platform is
designed so that is a future choice, not an upfront tax.

### Observability
- Structured JSON logs via [app/core/logging.py](app/core/logging.py)
- Notification delivery attempts captured per reminder (`channel`, `retries`)
- AI confidence stored on every extracted artifact and every timeline event
- Timeline payloads are queryable via `GET /v1/patients/{id}/timeline` with
  filtering by event type, urgency, actor caregiver, source, and time window

---

## Non-goals

Per CLAUDE.md, the following are **explicit non-goals** for the MVP and
will be refused in PRs:

- Telemedicine, video calling
- Insurance / billing workflows
- Hospital / EMR integrations
- Wearable integrations
- Autonomous agents, multi-agent orchestration
- Blockchain, crypto
- Emotional AI companions
- Medical diagnosis or treatment recommendation
- Microservices, Kubernetes, message brokers
- Generic "AI assistant" chat surfaces

Auth, RBAC, full audit log UI, and async workers are deferred — the data
model already supports them (`actor_caregiver_id` is everywhere, every
mutation produces a timeline event), so they can be added without rework.

---

## License

Portfolio / educational use. No HIPAA compliance is claimed.
