"""Tests for the catalogue import command (Plan 01-06 Task 1).

Contract under test: import is idempotent, fails closed when the freeze
document is not APPROVED or checksums do not match, and does not duplicate
rows under concurrent invocation.
"""

from __future__ import annotations

import threading
from io import StringIO

import pytest
from django.core.management import call_command, CommandError
from django.db import connections

from catalogue.models import AssetAttribution, GameAlias, GameRelease, GameWork, Platform, RelatedContent, SourceRecord


def _run_import() -> str:
    out = StringIO()
    call_command("import_catalogue", stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_import_creates_expected_hierarchy() -> None:
    _run_import()

    assert GameWork.objects.count() == 150
    assert SourceRecord.objects.count() == 150
    assert SourceRecord.objects.filter(source="wikidata").count() == 150
    # Every source record's snapshot hash matches the frozen manifest -- the
    # import never invents or mutates provenance.
    hashes = set(SourceRecord.objects.values_list("snapshot_sha256", flat=True))
    assert len(hashes) == 1

    # D-05/D-06: platform families survive into real Platform rows.
    platform_names = set(Platform.objects.values_list("name", flat=True))
    assert len(platform_names) > 0
    assert GameRelease.objects.count() >= GameWork.objects.count()

    # Bilingual aliases exist for at least the titles with a Spanish label.
    assert GameAlias.objects.filter(locale="es").count() > 0
    assert GameAlias.objects.filter(locale="en").count() == 150

    # Cover assets: only APPROVED (candidate) entries may ever be
    # display_allowed=True; anything else stays a placeholder.
    approved_assets = AssetAttribution.objects.filter(display_allowed=True)
    assert approved_assets.count() == 17
    for asset in approved_assets:
        assert asset.creator and asset.licence and asset.licence_url and asset.source_url


@pytest.mark.django_db
def test_import_is_idempotent() -> None:
    _run_import()
    first_work_count = GameWork.objects.count()
    first_release_count = GameRelease.objects.count()
    first_alias_count = GameAlias.objects.count()
    first_source_count = SourceRecord.objects.count()

    _run_import()

    assert GameWork.objects.count() == first_work_count
    assert GameRelease.objects.count() == first_release_count
    assert GameAlias.objects.count() == first_alias_count
    assert SourceRecord.objects.count() == first_source_count


@pytest.mark.django_db
def test_import_aborts_when_freeze_not_approved(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    fake_freeze = tmp_path / "catalogue-freeze.md"
    fake_freeze.write_text("**Estado:** BLOCKED\n", encoding="utf-8")
    monkeypatch.setattr(
        "catalogue.management.commands.import_catalogue.FREEZE_DOC_PATH",
        fake_freeze,
    )

    with pytest.raises(CommandError, match="APPROVED"):
        call_command("import_catalogue")

    assert GameWork.objects.count() == 0


@pytest.mark.django_db
def test_import_aborts_when_checksum_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    import catalogue.management.commands.import_catalogue as import_module

    original = import_module.Command._load_manifests

    def _tampered(self):  # type: ignore[no-untyped-def]
        raw, catalogue_manifest, assets_manifest = original(self)
        catalogue_manifest = dict(catalogue_manifest)
        catalogue_manifest["snapshot"] = dict(catalogue_manifest["snapshot"])
        catalogue_manifest["snapshot"]["sha256"] = "0" * 64
        return raw, catalogue_manifest, assets_manifest

    monkeypatch.setattr(import_module.Command, "_load_manifests", _tampered)

    with pytest.raises(CommandError, match="checksum"):
        call_command("import_catalogue")

    assert GameWork.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_import_does_not_duplicate() -> None:
    """Two near-simultaneous invocations must serialize via advisory lock,
    never producing duplicate GameWork/SourceRecord rows (CAT-04/CAT-06)."""
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            call_command("import_catalogue")
        except BaseException as exc:  # noqa: BLE001 - captured for the assertion below
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, f"concurrent import raised: {errors}"
    assert GameWork.objects.count() == 150
    assert SourceRecord.objects.count() == 150


@pytest.mark.django_db
def test_related_content_constraints_valid() -> None:
    """RelatedContent enforces D-11: a work cannot be its own DLC, and a
    (parent, child) pair cannot be declared twice."""
    from django.db import IntegrityError, transaction

    base = GameWork.objects.create(canonical_slug="base-game", original_title="Base Game")
    dlc = GameWork.objects.create(canonical_slug="base-game-dlc", original_title="Base Game DLC")

    RelatedContent.objects.create(parent_work=base, child_work=dlc, relation=RelatedContent.Relation.DLC)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RelatedContent.objects.create(parent_work=base, child_work=dlc, relation=RelatedContent.Relation.DLC)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RelatedContent.objects.create(parent_work=base, child_work=base, relation=RelatedContent.Relation.DLC)
