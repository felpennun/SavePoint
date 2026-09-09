"""Verify the active synthetic population and its frozen evaluation split."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from accounts.models import DemoAccountIdentity
from evaluation.protocol import load as load_protocol
from evaluation.splits import user_split
from evaluation.synthetic import SYNTHETIC_EVAL_USER_MARKER, SYNTHETIC_PHASE2_MARKER


class Command(BaseCommand):
    help = "Audit active synthetic-user isolation and the frozen train/validation/test split."

    def add_arguments(self, parser) -> None:  # noqa: ANN001
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument("--evidence-json", default=None)

    def handle(self, *args, **options) -> None:  # noqa: ANN002, ANN003
        corpus_version = options["corpus_version"]
        protocol = load_protocol()
        if protocol.corpus_version != corpus_version:
            raise CommandError(
                f"protocol corpus_version is {protocol.corpus_version!r}, "
                f"not {corpus_version!r}"
            )

        active = list(
            DemoAccountIdentity.objects.filter(marker=SYNTHETIC_EVAL_USER_MARKER)
            .order_by("user_id")
            .values_list("user_id", flat=True)
        )
        historical_ids = set(
            DemoAccountIdentity.objects.filter(marker=SYNTHETIC_PHASE2_MARKER)
            .values_list("user_id", flat=True)
        )
        active_ids = set(active)
        if active_ids & historical_ids:
            raise CommandError("active and historical synthetic populations overlap")

        expected = int(protocol.raw["synthetic_population"]["phase_3_population"])
        if len(active) != expected:
            raise CommandError(f"expected {expected} active users, got {len(active)}")

        split = user_split(active, protocol)
        split_counts = {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        }
        expected_split = {
            key: int(protocol.user_split[key]) for key in ("train", "validation", "test")
        }
        if split_counts != expected_split:
            raise CommandError(
                f"split counts {split_counts} do not match protocol {expected_split}"
            )

        evidence = {
            "audit": "synthetic-population-isolation",
            "corpus_version": corpus_version,
            "active_marker": SYNTHETIC_EVAL_USER_MARKER,
            "historical_marker": SYNTHETIC_PHASE2_MARKER,
            "active_user_count": len(active),
            "historical_phase2_user_count": len(historical_ids),
            "active_historical_overlap_count": len(active_ids & historical_ids),
            "protocol_expected_active_user_count": expected,
            "split": {
                "counts": split_counts,
                "seed": protocol.user_split_seed,
                "disjoint": (
                    not (set(split.train) & set(split.validation))
                    and not (set(split.train) & set(split.test))
                    and not (set(split.validation) & set(split.test))
                ),
                "covers_active_population": (
                    set(split.train) | set(split.validation) | set(split.test)
                ) == active_ids,
            },
            "runner_marker_query": "DemoAccountIdentity.marker == 'synthetic-eval-user'",
        }

        evidence_path = options.get("evidence_json")
        if evidence_path:
            path = Path(evidence_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.stdout.write(f"Wrote population isolation evidence to {path}")

        self.stdout.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
