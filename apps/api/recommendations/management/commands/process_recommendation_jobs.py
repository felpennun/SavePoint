"""Run the PostgreSQL-backed personalized recommendation refresh queue."""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from recommendations.jobs import process_one_job
from recommendations.published import SECTION_ALGORITHM_IDS, SIGNAL_ALGORITHM_ID


class Command(BaseCommand):
    help = "Process personalized recommendation refresh jobs."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument("--loop", action="store_true", help="Keep polling for new jobs.")
        parser.add_argument("--poll-seconds", type=float, default=2.0)
        parser.add_argument("--max-jobs", type=int, default=0, help="Stop after N jobs; 0 means no limit.")
        parser.add_argument(
            "--ondemand",
            action="store_true",
            help="Drain the queue holding the shared worker lock, then exit (no polling).",
        )
        parser.add_argument(
            "--algorithm-id",
            choices=(*SECTION_ALGORITHM_IDS, SIGNAL_ALGORITHM_ID),
            help="Process only this published recommendation section, or the signals job.",
        )

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        if options["ondemand"]:
            from recommendations.ondemand import drain_exclusive

            drained = drain_exclusive(lambda: process_one_job(options["algorithm_id"]))
            if drained is None:
                self.stdout.write("Another recommendation worker is running; nothing to do.")
            else:
                self.stdout.write(self.style.SUCCESS(f"Processed {drained} recommendation job(s)."))
            return
        processed = 0
        while True:
            if process_one_job(options["algorithm_id"]):
                processed += 1
                if options["max_jobs"] and processed >= options["max_jobs"]:
                    break
                continue
            if not options["loop"]:
                break
            time.sleep(max(0.1, min(float(options["poll_seconds"]), 60.0)))
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} recommendation job(s)."))
