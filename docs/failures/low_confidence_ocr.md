# Failure case: low-confidence OCR is *not* silently trusted

A core principle in [CLAUDE.md](../../CLAUDE.md):

> Human escalation is mandatory. If confidence is low: mark uncertain,
> request review, escalate to caregiver. Never silently invent medical
> information.

This document shows the exact path a low-confidence document upload takes
through the system, and what would have gone wrong if the pipeline had
trusted the AI output instead.

## Scenario

A caregiver photographs a handwritten prescription with poor lighting and
uploads it through `/v1/patients/{id}/documents`. The image is unreadable
enough that the OCR step produces a fragmented transcript.

## Pipeline trace

```
POST /v1/patients/2/documents      (binary upload)
  -> DocumentService.upload()
       writes document row, status=uploaded
       records timeline event: document_uploaded
  -> DocumentService.process()
       calls AIProvider.ocr()              -> confidence=0.55
       calls AIProvider.extract_medical_entities()  -> confidence=0.40
       combined = min(0.55, 0.40) = 0.40
       0.40 < CONFIDENCE_REVIEW_THRESHOLD (0.60)
       document.status = REVIEW_REQUIRED
       records timeline event: document_ocr_completed   (confidence=0.40)
           -> workflow engine fires rule_low_confidence_document
              -> records timeline event: document_review_required
              -> AlertService.raise_alert(urgency=MEDIUM,
                                          title="Document needs human review")
                 -> records timeline event: alert_raised
```

Inspectable end state:

| Artifact | Status / urgency | Visible to caregiver |
|---|---|---|
| `UploadedDocument` row | `status=review_required`, `confidence=0.40` | Documents page shows "review required" badge |
| Timeline | three new events: `document_uploaded` → `document_ocr_completed` → `document_review_required` | Timeline feed |
| Alert | medium-urgency, "Document needs human review" | Alerts page |

## What would have gone wrong without the gate

If the pipeline had trusted the extraction blindly:

1. The fragmented transcript might have produced a `medication_name`
   that does not match the prescription.
2. Downstream automation (a future "auto-create medication schedule from
   prescription" feature) would have scheduled the wrong drug or dosage.
3. The reminder workflow would have surfaced confidently incorrect prompts
   to the patient — the most dangerous failure mode in this domain.

## Why this fails *safely* instead

- **Confidence is structural, not advisory.** The threshold lives in
  [app/ai/providers.py](../../app/ai/providers.py) as a constant
  (`CONFIDENCE_REVIEW_THRESHOLD = 0.6`) and the document service code path
  (`status = REVIEW_REQUIRED if confidence < threshold`) makes the gate
  unbypassable from the AI provider.
- **The deterministic workflow engine, not the AI, decides escalation.**
  `app/workflows/engine.py::rule_low_confidence_document` reads the
  confidence off the timeline event and routes the document to a human.
  The AI provider has no path to suppress this.
- **The full path is auditable.** Three timeline events plus an alert row
  give the caregiver, and any downstream auditor, a complete record of
  *why* the document was held for review.

## Verifying this behaviour

Reproduce the case end to end:

```bash
python scripts/eval_rule_engine.py
# look for: [PASS] low_confidence_ocr
```

The scenario is also covered as a unit test in
[tests/test_workflow_engine.py](../../tests/test_workflow_engine.py) and as
an integration test in
[tests/test_documents_and_voice.py](../../tests/test_documents_and_voice.py).
