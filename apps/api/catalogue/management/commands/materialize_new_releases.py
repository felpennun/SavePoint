"""Recompute the home "Novedades" shelf snapshot (D-24).

Run this after an IGDB (re-)import -- and it also runs once in the
container startup chain. Between imports the shelf never changes, so
``NewReleasesView`` serves the row this command writes without recomputing
per request. Idempotent and advisory-lock guarded.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from catalogue.new_releases import materialize_new_releases


class Command(BaseCommand):
    help = "Recompute the home 'Novedades' shelf snapshot (run after an IGDB import)."

    def handle(self, *args: Any, **options: Any) -> None:
        snapshot = materialize_new_releases()
        self.stdout.write(
            self.style.SUCCESS(
                f"Novedades snapshot: {len(snapshot.work_ids)} works, "
                f"formula {snapshot.formula}, computed "
                f"{snapshot.computed_at:%Y-%m-%d %H:%M:%S}."
            )
        )
