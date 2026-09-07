"""Load the reviewed Spanish synopsis catalogue used by the bilingual demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogue.models import GameWork

REPO_ROOT = Path(__file__).resolve().parents[5]
SUMMARY_PATH = REPO_ROOT / "data" / "localization" / "summaries-es.json"


class Command(BaseCommand):
    help = "Load reviewed Spanish game summaries from the local translation manifest."

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            payload = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise CommandError("Spanish summary manifest is missing or invalid.") from exc
        if not isinstance(payload, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in payload.items()):
            raise CommandError("Spanish summary manifest must map slugs to text.")

        updated = 0
        with transaction.atomic():
            for slug, summary in payload.items():
                updated += GameWork.objects.filter(canonical_slug=slug).update(summary_es=summary.strip())
        self.stdout.write(self.style.SUCCESS(f"Loaded {updated} Spanish game summaries."))
