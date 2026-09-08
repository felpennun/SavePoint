"""Tests for the real-scale, resumable IGDB catalogue ingestion path
(Plan 01.1-02).

Task 1 (this first block) covers only the schema: the minimal ``Genre``
entity, its many-to-many attachment to ``GameWork``, and the durable
``IgdbImportRun`` checkpoint whose committed cursor is source/query scoped
and only ever moves forward. Works are always located by ``canonical_slug``
here, never by a fixed ``GameWork`` UUID.

Task 2 appends the importer/client behaviour tests to the same file.
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.db import DatabaseError, IntegrityError, transaction

from catalogue.igdb import IgdbClient, IgdbClientError, redact
from catalogue.models import (
    AssetAttribution,
    Developer,
    Franchise,
    GameAlias,
    GameRelease,
    GameWork,
    Genre,
    IgdbImportRun,
    Platform,
    SourceRecord,
)
from catalogue.normalization import normalize_title


# ---------------------------------------------------------------------------
# Task 1 -- schema: Genre membership and resumable IGDB checkpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_genre_is_unique_by_stable_igdb_identity() -> None:
    Genre.objects.create(igdb_id=12, name="Role-playing (RPG)", slug="role-playing-rpg")

    # Same IGDB identity must not be insertable twice, even with a different name.
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Genre.objects.create(igdb_id=12, name="RPG", slug="rpg")

    # A different IGDB identity is fine.
    with transaction.atomic():
        Genre.objects.create(igdb_id=31, name="Adventure", slug="adventure")

    assert Genre.objects.count() == 2


@pytest.mark.django_db
def test_genre_attaches_many_to_many_and_is_reachable_by_canonical_slug() -> None:
    work = GameWork.objects.create(canonical_slug="the-witcher-3", original_title="The Witcher 3")
    rpg = Genre.objects.create(igdb_id=12, name="Role-playing (RPG)", slug="role-playing-rpg")
    adventure = Genre.objects.create(igdb_id=31, name="Adventure", slug="adventure")

    work.genres.add(rpg, adventure)

    # Re-fetch strictly by canonical_slug -- no test may depend on the random UUID.
    reloaded = GameWork.objects.get(canonical_slug="the-witcher-3")
    assert set(reloaded.genres.values_list("igdb_id", flat=True)) == {12, 31}
    assert list(rpg.works.values_list("canonical_slug", flat=True)) == ["the-witcher-3"]


@pytest.mark.django_db
def test_import_run_checkpoint_is_scoped_by_source_and_query() -> None:
    IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0")

    # A different query identity under the same source is a distinct checkpoint.
    with transaction.atomic():
        IgdbImportRun.objects.create(source="igdb", query_identity="game_type=0;platform=6")

    assert IgdbImportRun.objects.count() == 2


@pytest.mark.django_db
def test_import_run_cursor_advances_monotonically_at_the_database_level() -> None:
    run = IgdbImportRun.objects.create(
        source="igdb", query_identity="game_type=0", last_committed_igdb_id=100
    )

    # Forward moves are accepted.
    run.last_committed_igdb_id = 250
    run.save(update_fields=["last_committed_igdb_id"])
    run.refresh_from_db()
    assert run.last_committed_igdb_id == 250

    # A backwards move is rejected by the database, not merely by Python.
    with pytest.raises(DatabaseError):
        with transaction.atomic():
            IgdbImportRun.objects.filter(pk=run.pk).update(last_committed_igdb_id=175)

    run.refresh_from_db()
    assert run.last_committed_igdb_id == 250


@pytest.mark.django_db
def test_import_run_cursor_cannot_be_created_negative() -> None:
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            IgdbImportRun.objects.create(
                source="igdb", query_identity="neg", last_committed_igdb_id=-1
            )


# ---------------------------------------------------------------------------
# Task 2 -- id-cursor batched import, client retry/redaction, freeze evidence
# ---------------------------------------------------------------------------


def _game(
    igdb_id: int,
    name: str,
    *,
    slug: str | None = None,
    genres: tuple[tuple[int, str], ...] = (),
    platforms: tuple[tuple[int, str], ...] = (),
    cover: str | None = None,
    first_release_date: int | None = None,
    rating: float | None = None,
    rating_count: int | None = None,
    total_rating_count: int | None = None,
    summary: str | None = None,
    alternative_names: tuple[str, ...] = (),
    title_en: str | None = None,
    franchises: tuple[tuple[int, str], ...] = (),
    developers: tuple[tuple[int, str], ...] = (),
) -> dict:
    row: dict = {"id": igdb_id, "name": name, "slug": slug or name.lower().replace(" ", "-")}
    row["url"] = f"https://www.igdb.com/games/{row['slug']}"
    if genres:
        row["genres"] = [{"id": gid, "name": gname} for gid, gname in genres]
    if platforms:
        row["platforms"] = [{"id": pid, "name": pname} for pid, pname in platforms]
    if cover:
        row["cover"] = {"image_id": cover}
    if first_release_date is not None:
        row["first_release_date"] = first_release_date
    if rating is not None:
        row["rating"] = rating
    if rating_count is not None:
        row["rating_count"] = rating_count
    if total_rating_count is not None:
        row["total_rating_count"] = total_rating_count
    if summary is not None:
        row["summary"] = summary
    if alternative_names:
        row["alternative_names"] = [{"name": value} for value in alternative_names]
    if title_en is not None:
        row["title_en"] = title_en
    if franchises:
        row["franchises"] = [{"id": item_id, "name": name} for item_id, name in franchises]
    if developers:
        row["involved_companies"] = [
            {"company": {"id": item_id, "name": name}, "developer": True}
            for item_id, name in developers
        ]
    return row


@pytest.mark.django_db
def test_igdb_import_maps_user_ratings_summary_and_reconciles_english_aliases() -> None:
    page = [[
        _game(
            909,
            "Café Quest",
            title_en="Cafe Quest",
            rating=87.5,
            rating_count=123,
            total_rating_count=140,
            summary="A short summary.",
            alternative_names=("Cafe Adventure", "Old Cafe Quest"),
        )
    ]]
    _run_import(FakeIgdbClient(page, eligible=1))

    work = GameWork.objects.get(canonical_slug="cafe-quest")
    assert work.rating == 87.5
    assert work.rating_count == 123
    assert work.total_rating_count == 140
    assert work.summary == "A short summary."
    assert normalize_title("Café Quest") in set(work.aliases.values_list("normalized_value", flat=True))
    assert normalize_title("Cafe Quest") in set(work.aliases.values_list("normalized_value", flat=True))
    assert normalize_title("Cafe Adventure") in set(work.aliases.values_list("normalized_value", flat=True))

    GameAlias.objects.create(
        work=work,
        locale="en",
        value="stale alias",
        normalized_value="stale alias",
    )
    GameAlias.objects.create(
        work=work,
        locale="es",
        value="Alias legado",
        normalized_value="alias legado",
    )
    changed = [[
        _game(
            909,
            "Café Quest",
            title_en="Cafe Quest",
            rating=88.0,
            rating_count=124,
            total_rating_count=141,
            summary="A changed summary.",
            alternative_names=("Cafe Adventure",),
        )
    ]]
    _run_import(FakeIgdbClient(changed, eligible=1))

    work.refresh_from_db()
    assert work.rating == 88.0
    assert work.summary == "A changed summary."
    assert not work.aliases.filter(normalized_value="stale alias").exists()
    assert work.aliases.filter(normalized_value="alias legado", locale="es").exists()
    assert work.aliases.filter(locale="en").count() == 2


@pytest.mark.django_db
def test_igdb_import_keeps_omitted_rating_fields_null() -> None:
    _run_import(FakeIgdbClient([[_game(910, "No Rating")]], eligible=1))
    work = GameWork.objects.get(canonical_slug="no-rating")
    assert work.rating is None
    assert work.rating_count is None
    assert work.total_rating_count is None


@pytest.mark.django_db
def test_igdb_import_persists_stable_franchises_and_developers() -> None:
    _run_import(
        FakeIgdbClient(
            [[
                _game(
                    911,
                    "Signal Quest",
                    franchises=((77, "Signal Saga"),),
                    developers=((88, "Signal Studio"),),
                )
            ]],
            eligible=1,
        )
    )

    work = GameWork.objects.get(canonical_slug="signal-quest")
    assert list(work.franchises.values_list("igdb_id", "slug")) == [(77, "signal-saga")]
    assert list(work.developers.values_list("igdb_id", "slug")) == [(88, "signal-studio")]
    assert Franchise.objects.count() == 1
    assert Developer.objects.count() == 1


class FakeIgdbClient:
    """In-memory IGDB stand-in: serves fixed pages by id-cursor, can be told
    to raise on a given page index to simulate an interruption/rate limit."""

    def __init__(
        self,
        pages: list[list[dict]],
        *,
        eligible: int | None = None,
        fail_on_page: int | None = None,
        error: Exception | None = None,
    ) -> None:
        self._pages = pages
        self._eligible = eligible if eligible is not None else sum(len(p) for p in pages)
        self._fail_on_page = fail_on_page
        self._error = error or IgdbClientError("simulated IGDB failure")
        self.page_calls = 0

    def count_eligible(self, where: str = "game_type = 0") -> int:
        return self._eligible

    def fetch_page(self, after_id: int, page_size: int = 500, where: str = "game_type = 0") -> list[dict]:
        for idx, page in enumerate(self._pages):
            if page and page[0]["id"] > after_id:
                if self._fail_on_page == idx:
                    raise self._error
                self.page_calls += 1
                return page
        return []


def _run_import(client: FakeIgdbClient, **kwargs) -> str:
    err = StringIO()
    call_command("import_igdb_catalogue", client=client, stderr=err, **kwargs)
    return err.getvalue()


def _two_full_pages() -> list[list[dict]]:
    return [
        [
            _game(10, "Alpha", genres=((12, "RPG"),), platforms=((6, "PC"), (48, "PS4")),
                  cover="cov10", first_release_date=1_500_000_000),
            _game(20, "Beta", genres=((12, "RPG"), (31, "Adventure")), platforms=((6, "PC"),)),
        ],
        [
            _game(30, "Gamma", platforms=((130, "Switch"),), cover="cov30",
                  first_release_date=1_600_000_000),
            _game(40, "Delta", genres=((31, "Adventure"),)),
        ],
    ]


@pytest.mark.django_db
def test_import_builds_catalogue_with_genres_platforms_and_cover_accounting() -> None:
    client = FakeIgdbClient(_two_full_pages(), eligible=4)
    _run_import(client)

    assert GameWork.objects.count() == 4
    assert SourceRecord.objects.filter(source="igdb").count() == 4
    assert set(SourceRecord.objects.values_list("source_id", flat=True)) == {"10", "20", "30", "40"}

    alpha = GameWork.objects.get(canonical_slug="alpha")
    assert set(alpha.genres.values_list("name", flat=True)) == {"RPG"}
    assert Platform.objects.filter(name="PC").exists()
    assert GameRelease.objects.filter(work=alpha).count() == 2

    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.eligible_count_live == 4
    assert run.works_imported == 4
    assert run.checksum and len(run.checksum) == 64
    # Every work has exactly one cover-accounting row; present + fallback == total.
    assert AssetAttribution.objects.filter(work__in=GameWork.objects.all()).count() == 4
    assert run.covers_present == 2
    assert run.covers_fallback == 2
    assert run.covers_present + run.covers_fallback == run.works_imported


@pytest.mark.django_db
def test_interrupted_import_resumes_from_last_committed_id_without_duplicates() -> None:
    interrupted = FakeIgdbClient(_two_full_pages(), eligible=4, fail_on_page=1)
    with pytest.raises(CommandError):
        _run_import(interrupted)

    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.status == IgdbImportRun.Status.FAILED
    assert run.last_committed_igdb_id == 20  # only the first page's batch committed
    assert GameWork.objects.count() == 2

    resumed = FakeIgdbClient(_two_full_pages(), eligible=4)
    _run_import(resumed)

    run.refresh_from_db()
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.last_committed_igdb_id == 40
    assert GameWork.objects.count() == 4
    assert SourceRecord.objects.filter(source="igdb").count() == 4

    # Checksum of a resumed-to-completion run equals a single clean full run.
    resumed_checksum = run.checksum
    call_command("import_igdb_catalogue", client=FakeIgdbClient(_two_full_pages(), eligible=4), stderr=StringIO())
    run.refresh_from_db()
    assert run.checksum == resumed_checksum


@pytest.mark.django_db
def test_malformed_record_is_skipped_not_fatal(tmp_path) -> None:
    import json

    pages = _two_full_pages()
    pages[1][0]["name"] = ""  # one unusable record in the second batch (id 30)
    out = tmp_path / "ev.json"
    _run_import(FakeIgdbClient(pages, eligible=4), evidence_json=str(out))

    # The poison row is skipped; every other row on both pages still imports,
    # and the run completes rather than wedging on the bad record.
    assert set(SourceRecord.objects.values_list("source_id", flat=True)) == {"10", "20", "40"}
    assert not GameWork.objects.filter(canonical_slug="gamma").exists()
    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.last_committed_igdb_id == 40  # cursor advances past the whole page
    assert json.loads(out.read_text())["malformed_skipped_this_pass"] == 1


@pytest.mark.django_db
def test_reimport_is_idempotent_and_convergent() -> None:
    client = FakeIgdbClient(_two_full_pages(), eligible=4)
    _run_import(client)
    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    first = (
        GameWork.objects.count(),
        SourceRecord.objects.count(),
        Genre.objects.count(),
        GameRelease.objects.count(),
        AssetAttribution.objects.count(),
        run.checksum,
    )

    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4))
    run.refresh_from_db()
    second = (
        GameWork.objects.count(),
        SourceRecord.objects.count(),
        Genre.objects.count(),
        GameRelease.objects.count(),
        AssetAttribution.objects.count(),
        run.checksum,
    )
    assert first == second


@pytest.mark.django_db
def test_chunked_reimport_after_complete_does_not_skip_the_committed_range() -> None:
    """Regression (repo-review 2026-09-06 H-02): a chunked re-import after a
    COMPLETE pass must rescan from id 0 and, if interrupted and resumed, pick
    up from *this pass's* cursor -- not jump forward to the stale monotonic
    high-water mark and silently skip everything below it."""
    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4))
    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.last_committed_igdb_id == 40

    # Re-import in one-batch chunks: the first chunk rescans page 1 (ids 10, 20)
    # and stops, resumable.
    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4), max_batches=1)
    run.refresh_from_db()
    assert run.status == IgdbImportRun.Status.INTERRUPTED
    assert run.pass_cursor == 20
    assert run.last_committed_igdb_id == 40  # monotonic guard unmoved

    # Simulate a page-2 row needing to be re-processed (an upstream change):
    # corrupt one of its works locally. A correct resume re-fetches page 2
    # and the upsert on id 30 restores it; the buggy resume jumps past id 40
    # and leaves the corruption in place.
    GameWork.objects.filter(canonical_slug="gamma").update(original_title="STALE-DO-NOT-KEEP")

    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4))
    run.refresh_from_db()
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.pass_cursor == 40
    assert GameWork.objects.get(canonical_slug="gamma").original_title == "Gamma", (
        "resume jumped past the committed range and skipped page 2"
    )
    assert SourceRecord.objects.filter(source="igdb").count() == 4


@pytest.mark.django_db
def test_import_coexists_with_preexisting_wikidata_platform_colliding_on_slug() -> None:
    """Regression (Plan 01.1-02 follow-up): the IGDB import must reconcile a
    shared lookup entity (Platform) on its natural key against a row that
    already exists from the Phase 1 Wikidata corpus.

    The Wikidata importer keys platforms on ``name`` and slugifies its
    lowercase label, producing ``name="web browser"`` / ``slug="web-browser"``.
    IGDB spells the same hardware "Web browser" -- same slug, different name.
    A blind ``get_or_create(name=...)`` misses the existing row and its INSERT
    trips ``catalogue_platform_slug_key``, aborting the whole run. The fix
    matches on ``slug`` first and reuses whatever row exists.
    """
    from django.utils.text import slugify

    # Exactly how import_catalogue (Wikidata) would have created it.
    wikidata_platform, _ = Platform.objects.get_or_create(
        name="web browser",
        defaults={"slug": slugify("web browser")[:150] or "platform"},
    )
    assert wikidata_platform.slug == "web-browser"

    pages = [[
        _game(501, "Browser Quest", platforms=((82, "Web browser"),)),
        _game(502, "Idle Tabs", platforms=((82, "Web browser"),)),
    ]]

    # No IntegrityError / CommandError may escape.
    _run_import(FakeIgdbClient(pages, eligible=2))

    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.status == IgdbImportRun.Status.COMPLETE

    # The pre-existing platform row is reused, never duplicated.
    assert Platform.objects.filter(slug="web-browser").count() == 1
    assert Platform.objects.get(slug="web-browser").pk == wikidata_platform.pk

    # Both IGDB games link their release to that same platform row.
    for work_slug in ("browser-quest", "idle-tabs"):
        work = GameWork.objects.get(canonical_slug=work_slug)
        assert list(work.releases.values_list("platform__slug", flat=True)) == ["web-browser"]

    # A re-run stays idempotent: still one platform row, still convergent.
    checksum = run.checksum
    _run_import(FakeIgdbClient(pages, eligible=2))
    run.refresh_from_db()
    assert run.status == IgdbImportRun.Status.COMPLETE
    assert run.checksum == checksum
    assert Platform.objects.filter(slug="web-browser").count() == 1
    assert GameRelease.objects.filter(platform__slug="web-browser").count() == 2


@pytest.mark.django_db
def test_slug_collision_produces_distinct_canonical_slugs() -> None:
    pages = [[
        _game(101, "Portal", slug="portal"),
        _game(202, "Portal", slug="portal"),
    ]]
    _run_import(FakeIgdbClient(pages, eligible=2))

    slugs = set(GameWork.objects.values_list("canonical_slug", flat=True))
    assert len(slugs) == 2
    assert "portal" in slugs
    assert any(s.startswith("portal-") for s in slugs)
    # Both remain resolvable by slug (never by UUID).
    assert GameWork.objects.get(canonical_slug="portal").source_records.get().source_id in {"101", "202"}


@pytest.mark.django_db
def test_missing_cover_falls_back_to_first_party_placeholder() -> None:
    pages = [[_game(7, "NoCover"), _game(8, "HasCover", cover="cov8")]]
    _run_import(FakeIgdbClient(pages, eligible=2))

    nocover = GameWork.objects.get(canonical_slug="nocover")
    asset = nocover.assets.get()
    assert asset.file_url == ""
    assert asset.display_allowed is False

    run = IgdbImportRun.objects.get(source="igdb", query_identity="game_type=0")
    assert run.covers_present == 1
    assert run.covers_fallback == 1
    assert run.covers_present + run.covers_fallback == run.works_imported


@pytest.mark.django_db
def test_dry_run_writes_nothing() -> None:
    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4), dry_run=True)
    assert GameWork.objects.count() == 0
    assert SourceRecord.objects.count() == 0
    assert not IgdbImportRun.objects.filter(status=IgdbImportRun.Status.COMPLETE).exists()


@pytest.mark.django_db
def test_evidence_json_is_emitted_with_measurements(tmp_path) -> None:
    import json

    out = tmp_path / "evidence.json"
    _run_import(FakeIgdbClient(_two_full_pages(), eligible=4), evidence_json=str(out))
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["query_identity"] == "game_type=0"
    assert payload["eligible_count_live"] == 4
    assert payload["primary_works_imported"] == 4
    assert payload["covers_present"] + payload["covers_fallback"] == 4
    assert len(payload["checksum_sha256"]) == 64
    assert payload["id_cursor_boundary"]["last_committed"] == 40
    assert payload["sampled_review_manifest"]  # deterministic, non-empty


# -- client-level behaviour: retry/backoff + redaction ---------------------


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    def __init__(self, responses: list) -> None:
        self._responses = list(responses)
        self.calls: list[str] = []
        self.call_kwargs: list[dict] = []

    def post(self, url, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append(url)
        self.call_kwargs.append(kwargs)
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def test_client_retries_rate_limit_then_succeeds_with_capped_backoff() -> None:
    sleeps: list[float] = []
    session = _FakeSession([
        _FakeResponse(200, {"access_token": "tok", "expires_in": 5000}),  # token
        _FakeResponse(429, text="Too Many Requests"),
        _FakeResponse(429, text="Too Many Requests"),
        _FakeResponse(200, {"count": 312418}),
    ])
    client = IgdbClient("cid", "csecret", session=session, sleep=lambda s: sleeps.append(s))

    assert client.count_eligible() == 312418
    backoffs = [s for s in sleeps if s >= 1.0]
    assert backoffs == [1.0, 2.0]  # exponential, and never exceeds the 60s cap


def test_client_error_messages_never_leak_credentials() -> None:
    boom = __import__("requests").ConnectionError(
        "failed connecting to id.twitch.tv/oauth2/token?client_id=cid&client_secret=SUPERSECRETVALUE "
        "with header Authorization: Bearer abc.def.ghi"
    )
    session = _FakeSession([boom, boom, boom, boom, boom])
    client = IgdbClient("cid", "SUPERSECRETVALUE", session=session, sleep=lambda _s: None)

    with pytest.raises(IgdbClientError) as excinfo:
        client.count_eligible()

    message = str(excinfo.value)
    assert "SUPERSECRETVALUE" not in message
    assert "client_secret=***" in message
    assert "Bearer ***" in message


def test_redact_helper_scrubs_known_shapes() -> None:
    raw = 'client_id=abc&client_secret=xyz "access_token": "t0ken" Authorization: Bearer h.e.a.d'
    scrubbed = redact(raw)
    assert "xyz" not in scrubbed
    assert "t0ken" not in scrubbed
    assert "client_secret=***" in scrubbed
    assert "Bearer ***" in scrubbed


def test_client_reuses_token_across_pages() -> None:
    session = _FakeSession([
        _FakeResponse(200, {"access_token": "tok", "expires_in": 5000}),
        _FakeResponse(200, [{"id": 1, "name": "A", "slug": "a"}]),
        _FakeResponse(200, [{"id": 2, "name": "B", "slug": "b"}]),
    ])
    client = IgdbClient("cid", "csecret", session=session, sleep=lambda _s: None)

    client.fetch_page(0)
    client.fetch_page(1)

    assert session.calls.count(TOKEN_URL := "https://id.twitch.tv/oauth2/token") == 1


def test_client_refuses_redirects_for_token_and_authenticated_requests() -> None:
    session = _FakeSession([
        _FakeResponse(200, {"access_token": "tok", "expires_in": 5000}),
        _FakeResponse(200, {"count": 1}),
    ])
    client = IgdbClient("cid", "csecret", session=session, sleep=lambda _s: None)

    assert client.count_eligible() == 1
    assert len(session.call_kwargs) == 2
    assert all(call["allow_redirects"] is False for call in session.call_kwargs)
