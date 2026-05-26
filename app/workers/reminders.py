"""CLI: expand today's reminders, dispatch due ones, detect missed doses.

This is intentionally a synchronous CLI rather than Celery — boring infra
per CLAUDE.md. Schedule it with cron / Windows Task Scheduler in real
deployments.

Usage:
    python -m app.workers.reminders --patient 1
    python -m app.workers.reminders --all
"""
from __future__ import annotations

import argparse
import logging

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.models.patient import Patient
from app.services.reminders import ReminderService

log = logging.getLogger("workers.reminders")


def run_for_patient(patient_id: int) -> dict[str, int]:
    with SessionLocal() as db:
        svc = ReminderService(db)
        expanded = svc.expand_for_patient(patient_id=patient_id)
        sent = svc.dispatch_due()
        missed = svc.detect_misses()
        return {"expanded": len(expanded), "sent": sent, "missed": missed}


def run_for_all() -> dict[int, dict[str, int]]:
    with SessionLocal() as db:
        ids = list(db.execute(select(Patient.id)).scalars())
    return {pid: run_for_patient(pid) for pid in ids}


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--patient", type=int, help="patient id to process")
    group.add_argument("--all", action="store_true", help="process all patients")
    args = parser.parse_args()

    if args.all:
        results = run_for_all()
        for pid, stats in results.items():
            log.info("patient %s -> %s", pid, stats)
    else:
        log.info("patient %s -> %s", args.patient, run_for_patient(args.patient))


if __name__ == "__main__":
    main()
