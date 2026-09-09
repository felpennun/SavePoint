"""Run the final read-only validation before recommender execution."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.models import DemoAccountIdentity
from catalogue.corpus import evaluation_candidate_works, governed_works
from evaluation.protocol import load as load_protocol
from evaluation.splits import user_split
from evaluation.synthetic import SYNTHETIC_EVAL_USER_MARKER, SYNTHETIC_PHASE2_MARKER
from recommendations.content.features import coverage_report


class Command(BaseCommand):
    help = "Validate and archive recommender inputs without running algorithms."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--validation-date", required=True)
        parser.add_argument("--evidence-json", required=True)

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        corpus_version = options["corpus_version"]
        try:
            validation_date = date.fromisoformat(options["validation_date"])
        except ValueError as exc:
            raise CommandError("--validation-date must be an ISO date") from exc

        protocol = load_protocol()
        failures: list[str] = []
        if protocol.corpus_version != corpus_version:
            failures.append("protocol corpus version differs")

        governed = governed_works(corpus_version)
        candidates = evaluation_candidate_works(corpus_version)
        governed_count = governed.count()
        candidate_count = candidates.count()
        governed_invalid_dates = governed.filter(
            Q(first_release_date__isnull=True) | Q(first_release_date__gt=validation_date)
        ).count()
        candidate_invalid_dates = candidates.filter(
            Q(first_release_date__isnull=True) | Q(first_release_date__gt=validation_date)
        ).count()
        candidate_invalid_rating_rule = candidates.filter(
            ~Q(total_rating_count__gte=1), rating__isnull=True
        ).count()
        if governed_invalid_dates:
            failures.append("governed corpus contains missing or future dates")
        if candidate_invalid_dates:
            failures.append("algorithm candidates contain missing or future dates")
        if candidate_invalid_rating_rule:
            failures.append("algorithm candidates violate the rating eligibility rule")

        active_ids = set(
            DemoAccountIdentity.objects.filter(marker=SYNTHETIC_EVAL_USER_MARKER)
            .values_list("user_id", flat=True)
        )
        historical_ids = set(
            DemoAccountIdentity.objects.filter(marker=SYNTHETIC_PHASE2_MARKER)
            .values_list("user_id", flat=True)
        )
        expected_population = int(protocol.raw["synthetic_population"]["phase_3_population"])
        split = user_split(active_ids, protocol)
        split_counts = {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        }
        expected_split = {
            key: int(protocol.user_split[key]) for key in ("train", "validation", "test")
        }
        if len(active_ids) != expected_population:
            failures.append("active synthetic population size differs from protocol")
        if active_ids & historical_ids:
            failures.append("active and historical synthetic populations overlap")
        if split_counts != expected_split:
            failures.append("synthetic user split differs from protocol")

        grid = protocol.grid
        modes = {mode: sum(entry["combine_mode"] == mode for entry in grid) for mode in (
            "weighted_sum", "multiplicative", "two_stage"
        )}
        recency_count = sum("recency_score" in entry.get("signals", []) for entry in grid)
        all_user_rating = all("user_rating" in entry.get("signals", []) for entry in grid)
        no_combined_rating = all("total_rating" not in entry.get("signals", []) for entry in grid)
        if len(grid) != 24 or modes != {"weighted_sum": 15, "multiplicative": 3, "two_stage": 6}:
            failures.append("tuning grid does not match the frozen 24-configuration contract")
        if recency_count != 6:
            failures.append("recency signal is not limited to the six recency configurations")
        if not all_user_rating or not no_combined_rating:
            failures.append("rating signals violate the user-rating-only contract")

        signals = coverage_report(corpus_version)
        if signals["feature_set_version"] != "fs-v5" or not signals["include_franchise"]:
            failures.append("saga/franchise signal is not active in fs-v5")

        evidence = {
            "audit": "recommender-input-preflight",
            "validation_date": validation_date.isoformat(),
            "corpus_version": corpus_version,
            "algorithm_execution": "not_run",
            "passed": not failures,
            "failures": failures,
            "corpus": {
                "governed_count": governed_count,
                "algorithm_candidate_count": candidate_count,
                "governed_invalid_date_count": governed_invalid_dates,
                "candidate_invalid_date_count": candidate_invalid_dates,
                "candidate_invalid_rating_rule_count": candidate_invalid_rating_rule,
            },
            "population": {
                "active_count": len(active_ids),
                "historical_phase2_count": len(historical_ids),
                "active_historical_overlap_count": len(active_ids & historical_ids),
                "split_counts": split_counts,
            },
            "protocol": {
                "protocol_version": protocol.protocol_version,
                "grid_count": len(grid),
                "grid_mode_counts": modes,
                "recency_configuration_count": recency_count,
                "all_configurations_use_user_rating": all_user_rating,
                "no_configuration_uses_combined_total_rating": no_combined_rating,
                "feature_set_version": signals["feature_set_version"],
            },
            "signal_coverage": signals,
        }
        path = Path(options["evidence_json"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.stdout.write(f"Wrote recommender preflight evidence to {path}")
        if failures:
            raise CommandError("preflight failed: " + "; ".join(failures))
        self.stdout.write(self.style.SUCCESS("Recommender input preflight passed; algorithms not run."))
