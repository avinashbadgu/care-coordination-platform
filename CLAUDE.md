# CLAUDE.md — AI Care Coordination & Workflow Intelligence Platform

# Project Identity

This is NOT:

* an AI doctor
* a diagnosis engine
* a symptom checker
* a medical recommendation system
* a generic healthcare chatbot

This project is:

> an AI-assisted care coordination and operational workflow platform.

The system exists to reduce:

* fragmented caregiving communication
* missed medications
* unstructured medical information
* caregiver coordination failures
* delayed escalations
* operational overload in home-care environments

The product value is operational coordination, not medical intelligence.

AI is a supporting layer.

Workflows are the core product.

---

# Core Product Vision

A centralized operational system for:

* patients
* family caregivers
* nurses
* caretakers

that transforms:

* reminders
* reports
* voice notes
* prescriptions
* care plans
* escalations

into:

* structured workflows
* timeline events
* actionable alerts
* measurable adherence

The project should feel like:

> caregiving infrastructure software

NOT:

> another AI chatbot demo.

---

# Primary Product Goals

The MVP must focus on these pillars:

## 1. Unified Care Timeline

A complete operational history of patient-related events.

## 2. Medication Workflow Engine

Reminder → confirmation → escalation pipeline.

## 3. Care Plan Management

Track adherence against doctor/caregiver-defined plans.

## 4. Document Intelligence

OCR + extraction + structured medical entity parsing.

## 5. Voice Note Intelligence

Speech-to-text → extraction → timeline updates.

## 6. Smart Escalation System

Operational risk detection and escalation routing.

## 7. Multi-Caregiver Coordination

Shared responsibilities, auditability, and notifications.

## 8. Daily AI Summaries

Operational summaries for caregivers and families.

---

# Product Philosophy

## 1. Workflow-first, chat-second

The primary UX is:

* timelines
* reminders
* alerts
* tasks
* summaries
* escalations
* reports

Chat interfaces are secondary.

Do NOT architect the platform around conversations.

---

## 2. AI augments operations

AI should:

* summarize
* extract
* prioritize
* classify
* organize
* detect anomalies
* reduce cognitive load

AI should NOT:

* diagnose
* prescribe
* recommend treatment
* hallucinate medical facts
* pretend certainty

---

## 3. Human escalation is mandatory

If confidence is low:

* mark uncertain
* request review
* escalate to caregiver

Never silently invent medical information.

---

## 4. Event-driven architecture is the backbone

Every meaningful action becomes a typed event.

Examples:

* medication_taken
* medication_missed
* escalation_triggered
* report_uploaded
* transcription_completed
* reminder_failed
* abnormal_reading_detected
* caregiver_notified
* appointment_created

The timeline is the source of truth.

---

# MVP Scope

The MVP includes ONLY:

## Care timeline

Chronological operational history.

## Medication scheduling

Reminders, adherence tracking, escalation.

## Care plan tracking

Task adherence against structured plans.

## Document upload + OCR

Prescription/report processing.

## Voice-note processing

Transcription + structured extraction.

## Alert prioritization

Low / medium / high urgency.

## Multi-user coordination

Basic caregiver roles and permissions.

## Daily summaries

AI-generated operational digests.

---

# Explicit Non-Goals (MVP)

Do NOT build:

* telemedicine
* video calling
* insurance workflows
* hospital integrations
* wearable integrations
* autonomous agents
* multi-agent orchestration
* blockchain
* crypto
* emotional AI companions
* medical diagnosis systems
* over-engineered microservices
* Kubernetes
* generic “AI assistant” chat

Avoid architecture inflation.

---

# High-Level Architecture

```text
                    AI Care Coordination Platform
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼

  Workflow Engine          AI Processing Layer         Timeline Engine
  reminders/escalations    OCR/STT/extraction          event history/search

        ▼                          ▼                          ▼

 Notification Layer       Risk Prioritization         Analytics Dashboard

                                   ▼

                         Observability + Audit Logs
```

---

# System Architecture Principles

## 1. Prefer boring infrastructure

Use:

* FastAPI
* PostgreSQL
* SQLAlchemy 2
* Alembic
* Redis only if needed
* Celery / ARQ for background jobs if required

Avoid:

* premature microservices
* distributed complexity
* unnecessary event brokers
* Kubernetes-level orchestration

This is a portfolio project.

Not hyperscale infrastructure.

---

## 2. Keep AI modules isolated

Separate services/pipelines for:

* OCR
* transcription
* extraction
* summarization
* prioritization

Never create one giant AI service.

---

## 3. Explicit workflows over framework magic

Bad:

* hidden orchestration
* magical abstractions
* unclear side effects

Good:

* typed events
* observable stages
* deterministic workflows
* explicit state transitions

---

## 4. Timeline-centric data model

The timeline is a first-class feature.

Every major action should generate:

* structured event
* metadata
* audit trail

The system should be debuggable from timeline history alone.

---

# Core Data Model

The platform revolves around:

## Patient

Core patient entity.

## Caregiver

Family member / nurse / caretaker.

## CarePlan

Doctor/caregiver-defined operational plan.

## TimelineEvent

Canonical operational event log.

## MedicationSchedule

Structured medication timing + dosage.

## Reminder

Reminder delivery + acknowledgement tracking.

## UploadedDocument

Prescription/report storage + extraction.

## VoiceNote

Audio upload + transcript + extraction.

## Alert

Operational urgency object.

## Escalation

Escalation workflow state.

## DailySummary

Generated operational digest.

---

# AI Processing Pipelines

# 1. OCR & Document Intelligence

Input:

* prescription
* PDF report
* lab image

Pipeline:

```text
document
  → OCR
  → text cleanup
  → medical entity extraction
  → confidence scoring
  → timeline event generation
```

Extract:

* medicines
* dosage
* frequency
* test values
* doctor names
* dates

Output:

* structured entities
* extracted raw text
* confidence score
* operational summary

Low-confidence extraction must require review.

---

# 2. Voice Note Intelligence

Input:

* caregiver voice note

Pipeline:

```text
audio
  → transcription
  → entity extraction
  → summarization
  → timeline event creation
  → follow-up action detection
```

Example:

```text
"Mom skipped insulin today and felt dizzy after lunch"
```

Becomes:

* medication_missed event
* symptom_detected event
* medium/high-priority alert

---

# 3. Daily Summary Generation

Every day:
generate operational summaries.

Example:

```text
Daily Summary:
- 3/4 medications completed
- insulin missed at 8 PM
- one abnormal BP reading detected
- follow-up appointment tomorrow
- caregiver escalation triggered once
```

Purpose:
reduce caregiver cognitive overload.

---

# 4. Risk & Escalation Engine

The engine is operational, NOT diagnostic.

Inputs:

* missed medications
* abnormal readings
* adherence trends
* reminder failures
* extracted report signals

Outputs:

* urgency classification
* escalation routing
* follow-up recommendation

---

# Escalation Policy Engine

Support rule-based escalation.

Examples:

```text
IF insulin missed twice in 24h
AND glucose abnormal
THEN high-priority escalation
```

```text
IF medication missed once
THEN notify caregiver
```

The rules engine is deterministic.

AI may assist prioritization but should not control critical logic.

---

# Multi-Caregiver Coordination

Support:

* family
* caretaker
* nurse

Role examples:

## Patient

Receives reminders.

## Caregiver

Confirms tasks, uploads reports.

## Family Member

Receives escalations and summaries.

## Admin

Manages care plans and workflows.

Every action must be attributable.

---

# Audit & Accountability

Track:

* who confirmed medication
* who ignored reminders
* escalation history
* notification delivery
* extraction edits
* care-plan modifications

This is operational infrastructure.

Auditability matters.

---

# Timeline Search & Retrieval

Semantic retrieval is justified ONLY here.

Search over:

* reports
* summaries
* voice notes
* events
* alerts

Example:

```text
"When was insulin dosage changed?"
```

Avoid generic chatbot retrieval.

---

# Notification Reliability Layer

Track:

* delivery success
* retries
* fallback routing
* notification latency

Example:

```text
push failed
→ SMS fallback
→ caregiver escalation
```

Operational reliability matters more than flashy AI.

---

# Observability Requirements

Log:

* reminder delivery
* escalation triggers
* OCR failures
* extraction confidence
* AI processing latency
* failed transcriptions
* notification retries
* background-job failures

Operational visibility is mandatory.

---

# Evaluation Philosophy

Every AI subsystem should eventually have measurable evaluation.

Examples:

## OCR

* extraction accuracy
* confidence calibration

## STT

* transcription quality

## Entity extraction

* precision / recall

## Escalation system

* false positive rate
* missed escalation rate

## Reminder system

* adherence success rate

Avoid unmeasured AI features.

---

# UX Philosophy

The interface should feel:

* calm
* readable
* trustworthy
* operational

Avoid:

* sci-fi aesthetics
* excessive chatbot framing
* AI gimmicks
* animation-heavy UI

Prioritize:

* timelines
* alerts
* summaries
* adherence tracking
* actionable workflows

---

# Security & Privacy Principles

Even as a portfolio project:

* avoid storing secrets in code
* use env vars everywhere
* structure DB access carefully
* isolate uploads
* validate file uploads
* sanitize OCR text before processing

Never pretend to be HIPAA compliant unless you actually are.

---

# Code Quality Rules

* Strong typing everywhere
* Pydantic schemas at boundaries
* Thin routes, thick services
* Background jobs isolated
* Version prompts
* Explicit workflow orchestration
* Modular AI pipelines
* Test critical business logic
* Avoid giant service classes

---

# What Makes This Project Strong

This project demonstrates:

* operational systems design
* workflow orchestration
* event-driven architecture
* multimodal AI integration
* observability discipline
* AI reliability thinking
* escalation system design
* realistic AI constraints

NOT:

* AI buzzword stacking
* framework hype
* giant-agent architectures

---

# Final Guiding Principle

The system should feel like:

> operational infrastructure for caregiving coordination

not:

> an AI chatbot pretending to be a doctor.

