"""Offline, single-run evaluation command (EVAL-01, EVAL-10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from evaluation import protocol
from evaluation.runner import SnapshotCoverageError, run


class Command(BaseCommand):
    help = "Run the frozen ranking comparison over synthetic evaluation users."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument(
            "--split", choices=("validation", "test"), default="test",
            help="validation is for tuning; test is the one-shot final comparison",
        )
        parser.add_argument(
            "--evidence-json", default="",
            help="write evidence to this path; '-' writes pure JSON to stdout",
        )
        parser.add_argument(
            "--force-new-protocol", action="store_true",
            help="bump protocol_version and clear the consumed-test marker",
        )
        parser.add_argument(
            "--marker-path", default="",
            help="override the local test-consumption marker path (tests only)",
        )

    @staticmethod
    def _marker_path(option: str) -> Path:
        return Path(option) if option else Path(settings.BASE_DIR) / ".evaluation-test-run.json"

    @staticmethod
    def _bump_protocol() -> None:
        path = protocol.default_protocol_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["protocol_version"] = int(raw["protocol_version"]) + 1
            path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError(f"cannot bump protocol_version: {exc}") from exc

    def _emit_evidence(self, target: str, artifact: dict[str, Any]) -> None:
        blob = json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if target == "-":
            self.stdout.write(blob, ending="")
            return
        if not target:
            return
        path = Path(target)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(blob, encoding="utf-8")
        except OSError as exc:
            raise CommandError(f"cannot write evaluation evidence: {exc}") from exc
        self.stderr.write(f"evidence written: {path}")

    def handle(self, *args: Any, **options: Any) -> None:
        corpus_version = options["corpus_version"]
        marker_path = self._marker_path(options.get("marker_path", ""))
        if options.get("force_new_protocol"):
            self._bump_protocol()
            marker_path.unlink(missing_ok=True)

        try:
            frozen = protocol.load(
                test_run_marker=marker_path,
                allow_consumed_test=False,
            )
            if frozen.corpus_version and frozen.corpus_version != corpus_version:
                raise CommandError(
                    "--corpus-version does not match the corpus_version frozen in protocol.json"
                )
            artifact = run(frozen, corpus_version, split=options["split"])
        except (protocol.ProtocolError, SnapshotCoverageError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        self._emit_evidence(options.get("evidence_json", ""), artifact)
        if options["split"] == "test":
            protocol.record_test_run(marker_path, frozen)
        if not options.get("evidence_json"):
            self.stdout.write(json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True))
        elif options["evidence_json"] != "-":
            self.stdout.write(self.style.SUCCESS("Evaluation completed"))
