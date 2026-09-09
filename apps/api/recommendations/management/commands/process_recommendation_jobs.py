"""Run the PostgreSQL-backed personalized recommendation refresh queue."""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand

from recommendations.jobs import process_one_job


class Command(BaseCommand):
    help = "Process personalized recommendation refresh jobs."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument("--loop", action="store_true", help="Keep polling for new jobs.")
        parser.add_argument("--poll-seconds", type=float, default=2.0)
        parser.add_argument("--max-jobs", type=int, default=0, help="Stop after N jobs; 0 means no limit.")

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        processed = 0
        while True:
            if process_one_job():
                processed += 1
                if options["max_jobs"] and processed >= options["max_jobs"]:
                    break
                continue
            if not options["loop"]:
                break
            time.sleep(max(0.1, min(float(options["poll_seconds"]), 60.0)))
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} recommendation job(s)."))
