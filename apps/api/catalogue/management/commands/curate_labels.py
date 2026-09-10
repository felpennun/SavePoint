"""Publish the initial unified editorial label vocabulary."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Iterable

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils.text import slugify

from catalogue.curated_labels import (
    CURATED_LABELS,
    CURATED_LABEL_VERSION,
    GAME_MODE_RULES,
    GENRE_RULES,
    PLAYER_PERSPECTIVE_RULES,
    THEME_RULES,
    curation_manifest,
    lookup_key,
)
from catalogue.models import (
    CuratedLabel,
    GameMode,
    GameWork,
    GameWorkCuratedLabel,
    Genre,
    PlayerPerspective,
    Subgenre,
    Theme,
)


CURATION_LOCK_KEY = 902_020_204

# Existing curated subgenres are used as the only keyword-derived evidence.
# Raw keyword aliases must first pass through the versioned subgenre curation
# command; this command never promotes Keyword rows directly.
SUBGENRE_RULES: dict[str, tuple[str, ...]] = {
    "1990s": ("Retro",),
    "1-bit": ("Retro",),
    "action rpg": ("Action", "RPG"),
    "action adventure": ("Action", "Adventure"),
    "action roguelike": ("Action", "Roguelike"),
    "anime": ("Anime",),
    "autobattler": ("Strategy",),
    "autochess": ("Strategy",),
    "casual": ("Casual",),
    "card game": ("Card Game",),
    "deckbuilding": ("Deckbuilder",),
    "dungeons & dragons": ("Fantasy",),
    "hidden object": ("Puzzle",),
    "family friendly": ("Family Friendly",),
    "jrpg": ("JRPG",),
    "lovecraft": ("Horror",),
    "psychological horror": ("Horror",),
    "match3": ("Puzzle",),
    "metroidvania": ("Metroidvania",),
    "minigolf": ("Sports",),
    "old school": ("Retro",),
    "online co-op": ("Co-op", "Multiplayer"),
    "pacman": ("Arcade",),
    "pixelart": ("Pixel Art",),
    "post-apocalyptic": ("Survival",),
    "roguelike": ("Roguelike",),
    "roguelike deckbuilding": ("Roguelike", "Deckbuilder"),
    "rollercoaster": ("Simulation",),
    "shoot'em up": ("Shooter",),
    "sidescroller": ("Side Scroller",),
    "spacecombat": ("Sci-fi",),
    "spaceship": ("Sci-fi",),
    "souls-like": ("Souls-like",),
    "story rich": ("Story Rich",),
    "swordsorcery": ("Fantasy",),
    "superhero": ("Superhero",),
    "turn-based": ("Turn-Based",),
    "music and rhythm": ("Music",),
    "bullet hell": ("Shooter",),
    "tower defense": ("Strategy",),
    "cyberpunk": ("Cyberpunk",),
    "survival horror": ("Horror", "Survival"),
    "brawler": ("Hack and Slash",),
    "turn-based rpg": ("RPG", "Turn-Based"),
    "2d platformer": ("Platformer",),
    "dark fantasy": ("Fantasy",),
    "dating simulation": ("Simulation",),
    "city builder": ("Simulation", "Strategy"),
    "precision platforming": ("Platformer",),
    "puzzle platformer": ("Platformer", "Puzzle"),
    "wargame": ("Strategy",),
}


class Command(BaseCommand):
    help = "Publish the versioned unified editorial label mapping."
    requires_system_checks: list = []

    def add_arguments(self, parser: Any) -> None:
        base_version_action = parser._option_string_actions.get("--version")
        if base_version_action is not None:
            parser._handle_conflict_resolve(None, [("--version", base_version_action)])
        parser.add_argument("--version", default=CURATED_LABEL_VERSION)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--evidence-json", default="-")

    def _emit(self, path: str, report: dict[str, object]) -> None:
        blob = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path == "-":
            self.stdout.write(blob, ending="")
            return
        from pathlib import Path

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(blob, encoding="utf-8")
        self.stderr.write(f"curated label evidence written: {target}")

    @staticmethod
    def _add_relation_evidence(
        *,
        objects: Iterable[Any],
        rule_map: dict[str, tuple[str, ...]],
        relation_name: str,
        add_evidence: Any,
    ) -> None:
        source_kinds = {
            "genres": "genre",
            "themes": "theme",
            "game_modes": "game_mode",
            "player_perspectives": "player_perspective",
            "subgenres": "subgenre",
        }
        source_kind = source_kinds[relation_name]
        for source in objects:
            labels = rule_map.get(lookup_key(source.name))
            if not labels:
                continue
            work_ids = GameWork.objects.filter(
                **{f"{relation_name}__id": source.pk}
            ).values_list("pk", flat=True)
            for label_name in labels:
                for work_id in work_ids:
                    add_evidence(work_id, label_name, source_kind, source.name)

    def handle(self, *args: Any, **options: Any) -> None:
        version = str(options["version"])
        dry_run = bool(options["dry_run"])
        label_names = {name for name, _ in CURATED_LABELS}
        label_kinds = dict(CURATED_LABELS)

        label_work_ids: dict[str, set[Any]] = defaultdict(set)
        evidence_counts: dict[str, int] = defaultdict(int)
        seen_evidence: set[tuple[Any, str, str, str]] = set()
        pending: list[GameWorkCuratedLabel] = []

        def add_evidence(work_id: Any, label_name: str, source_kind: str, source_value: str) -> None:
            if label_name not in label_names:
                raise ValueError(f"Rule references an undeclared label: {label_name}")
            key = (work_id, label_name, source_kind, source_value)
            if key in seen_evidence:
                return
            seen_evidence.add(key)
            label_work_ids[label_name].add(work_id)
            evidence_counts[label_name] += 1
            if not dry_run:
                pending.append(
                    GameWorkCuratedLabel(
                        work_id=work_id,
                        label_id=labels_by_name[label_name].pk,
                        source_kind=source_kind,
                        source_value=source_value,
                    )
                )

        labels_by_name: dict[str, CuratedLabel] = {}
        if not dry_run:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CURATION_LOCK_KEY])
                GameWorkCuratedLabel.objects.all().delete()
                CuratedLabel.objects.all().delete()
                CuratedLabel.objects.bulk_create(
                    [
                        CuratedLabel(
                            name=name,
                            slug=slugify(name),
                            kind=kind,
                            curation_version=version,
                        )
                        for name, kind in CURATED_LABELS
                    ]
                )
                labels_by_name = {label.name: label for label in CuratedLabel.objects.all()}
        else:
            labels_by_name = {
                name: CuratedLabel(name=name, slug=slugify(name), kind=kind, curation_version=version)
                for name, kind in CURATED_LABELS
            }

        self._add_relation_evidence(
            objects=Genre.objects.all(),
            rule_map={lookup_key(key): value for key, value in GENRE_RULES.items()},
            relation_name="genres",
            add_evidence=add_evidence,
        )
        self._add_relation_evidence(
            objects=Theme.objects.all(),
            rule_map={lookup_key(key): value for key, value in THEME_RULES.items()},
            relation_name="themes",
            add_evidence=add_evidence,
        )
        self._add_relation_evidence(
            objects=GameMode.objects.all(),
            rule_map={lookup_key(key): value for key, value in GAME_MODE_RULES.items()},
            relation_name="game_modes",
            add_evidence=add_evidence,
        )
        self._add_relation_evidence(
            objects=PlayerPerspective.objects.all(),
            rule_map={lookup_key(key): value for key, value in PLAYER_PERSPECTIVE_RULES.items()},
            relation_name="player_perspectives",
            add_evidence=add_evidence,
        )
        self._add_relation_evidence(
            objects=Subgenre.objects.all(),
            rule_map={lookup_key(key): value for key, value in SUBGENRE_RULES.items()},
            relation_name="subgenres",
            add_evidence=add_evidence,
        )

        if not dry_run:
            with transaction.atomic():
                GameWorkCuratedLabel.objects.bulk_create(pending, batch_size=5000)

        report = {
            "curation_version": version,
            "mapping_sha256": curation_manifest()["sha256"],
            "dry_run": dry_run,
            "label_count": len(CURATED_LABELS),
            "labels": [
                {
                    "name": name,
                    "kind": label_kinds[name],
                    "work_count": len(label_work_ids[name]),
                    "evidence_count": evidence_counts[name],
                }
                for name, _ in CURATED_LABELS
            ],
            "assigned_work_count": len(set().union(*label_work_ids.values())) if label_work_ids else 0,
            "assignment_count": len(seen_evidence),
            "labels_without_assignments": [
                name for name, _ in CURATED_LABELS if not label_work_ids[name]
            ],
            "manifest": curation_manifest(),
        }
        self._emit(str(options["evidence_json"]), report)
