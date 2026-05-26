"""CLI: generate daily summaries for one or all patients.

Usage:
    python -m app.workers.summaries --patient 1
    python -m app.workers.summaries --all
"""
from __future__ import annotations

import argparse
import logging
from datetime import date

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.models.patient import Patient
from app.services.summaries import SummaryService

log = logging.getLogger("workers.summaries")


def run_for_patient(patient_id: int, target_date: date | None = None) -> int:
    with SessionLocal() as db:
        summary = SummaryService(db).generate(
            patient_id=patient_id, target_date=target_date
        )
        return summary.id


def run_for_all(target_date: date | None = None) -> dict[int, int]:
    with SessionLocal() as db:
        ids = list(db.execute(select(Patient.id)).scalars())
    return {pid: run_for_patient(pid, target_date) for pid in ids}


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--patient", type=int)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--date", type=date.fromisoformat, default=None)
    args = parser.parse_args()

    if args.all:
        log.info("summaries -> %s", run_for_all(args.date))
    else:
        log.info(
            "patient %s summary id=%s",
            args.patient,
            run_for_patient(args.patient, args.date),
        )


if __name__ == "__main__":
    main()
