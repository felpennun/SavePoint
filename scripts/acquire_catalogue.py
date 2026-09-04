#!/usr/bin/env python3
"""Acquire a review-only Wikidata/Commons catalogue candidate.

This command is deliberately offline from the application runtime. It writes
versioned JSON candidates only; it never connects to PostgreSQL and never marks
external media as approved.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "wikidata-games.json"
CATALOGUE_MANIFEST = ROOT / "data" / "manifests" / "catalogue.json"
ASSET_MANIFEST = ROOT / "data" / "manifests" / "assets.json"

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
ALLOWED_HOSTS = frozenset({"query.wikidata.org", "commons.wikimedia.org"})
USER_AGENT = "SavePoint-TFG/0.1 (academic dataset acquisition; contact: repository issue tracker)"
MAX_BYTES = 20 * 1024 * 1024
TIMEOUT_SECONDS = 90
MAX_REDIRECTS = 2
TARGET_COUNT = 150
MIN_COUNT = 100
MAX_COUNT = 300
RETRIEVED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# revision 4: revision 3's hand-curated VALUES list was found (during a live acquisition
# run) to contain QIDs that are not video games at all -- e.g. Q4945 (a French commune),
# Q9371 (spleen, the organ), Q49100 (the Yom Kippur War) -- because the list was authored
# without verifying each QID resolves to an actual game. Revision 4 replaces the fabricated
# VALUES list with a `?game wdt:P31 wd:Q7889` ("instance of video game") class filter, run as
# several small bounded queries instead of one broad query, so D-05/D-06 era/platform coverage
# is guaranteed by construction rather than hoped for from whatever a single LIMIT happens to
# return. Each query avoids the wikibase:sitelinks join that caused revision <3's timeout.
_BASE_TEMPLATE = """# SavePoint Phase 1 candidate query, revision 4 ({label})
SELECT ?game ?enLabel ?esLabel (MIN(?date) AS ?releaseDate)
       (SAMPLE(?candidateImage) AS ?image) WHERE {{
  ?game wdt:P31 wd:Q7889 .
{extra}
  ?game rdfs:label ?enLabel . FILTER(LANG(?enLabel) = "en")
  OPTIONAL {{ ?game rdfs:label ?esLabel . FILTER(LANG(?esLabel) = "es") }}
  OPTIONAL {{ ?game wdt:P577 ?date }}
  OPTIONAL {{ ?game wdt:P18 ?candidateImage }}
}}
GROUP BY ?game ?enLabel ?esLabel
LIMIT {limit}
"""

# Platform sub-queries resolve target platform QIDs at runtime via Wikidata's own
# search backend (see `_resolve_platform_qids`) rather than a hand-typed QID list --
# revision 3's fabricated VALUES list is exactly the failure mode this avoids: a QID
# typed from memory without verification can silently denote something else entirely
# (a commune, an organ, a war). A raw `CONTAINS(LCASE(?platformLabel), "xbox")` scan
# over every game's every platform was tried first and reliably 504-timed-out on the
# public endpoint (it has no index to exploit); resolving a small set of verified
# platform QIDs first, then joining games via `VALUES ?platform {...}`, is a bounded,
# indexed lookup instead of a full scan.
_PLATFORM_VALUES_EXTRA = """  ?game wdt:P400 ?platform .
  VALUES ?platform {{ {platform_qids} }}
"""


def _resolve_platform_qids(search_term: str, limit: int = 8) -> dict[str, str]:
    """Resolve real, verified platform QIDs for a search term via Wikidata's own
    search index (SERVICE wikibase:mwapi), keeping only entities actually used as
    the wdt:P400 platform of at least one real P31=Q7889 video game. Both the
    search and the verification stay within ALLOWED_HOSTS (query.wikidata.org)."""
    query = f"""SELECT DISTINCT ?item ?itemLabel WHERE {{
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:api "EntitySearch" .
    bd:serviceParam wikibase:endpoint "www.wikidata.org" .
    bd:serviceParam mwapi:search "{search_term}" .
    bd:serviceParam mwapi:language "en" .
    ?item wikibase:apiOutputItem mwapi:item .
  }}
  ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en")
  FILTER EXISTS {{ ?anygame wdt:P31 wd:Q7889 ; wdt:P400 ?item }}
}}
LIMIT {limit}
"""
    response = _fetch_json(WIKIDATA_ENDPOINT, {"query": query, "format": "json"})
    bindings = response.get("results", {}).get("bindings") or []
    resolved: dict[str, str] = {}
    for binding in bindings:
        uri = _binding_value(binding, "item")
        label = _binding_value(binding, "itemLabel")
        if uri and label:
            resolved[_qid(uri)] = label
    return resolved


def _build_platform_query(label: str, search_terms: list[str], limit: int) -> tuple[str, str, int] | None:
    """Resolve QIDs for every search term and build a bounded games sub-query.
    Returns None (skip this sub-query) if nothing verifiable was found -- never
    fabricate a fallback QID."""
    resolved: dict[str, str] = {}
    for term in search_terms:
        resolved.update(_resolve_platform_qids(term))
    if not resolved:
        print(f"  platform resolution for '{label}': no verified QIDs found, skipping")
        return None
    print(f"  platform resolution for '{label}': {resolved}")
    values = " ".join(f"wd:{qid}" for qid in resolved)
    extra = _PLATFORM_VALUES_EXTRA.format(platform_qids=values)
    return (label, extra, limit)


# Bounded sub-queries: one broad sweep plus targeted eras/platforms known to be
# under-represented in a random sample, so the required D-05/D-06 matrix is met
# by construction. Coverage-critical queries run FIRST so `_aggregate`'s
# insertion-order truncation (see its final `list(...)[:TARGET_COUNT]` step) keeps
# them even when the broad sweep alone would already exceed TARGET_COUNT; the
# broad sweep runs last and only fills whatever slots remain. Platform queries are
# resolved dynamically (see `_build_platform_query`) so they carry no static list.
STATIC_ACQUISITION_QUERIES: list[tuple[str, str, int]] = [
    ("pre-1990 era", '  ?game wdt:P577 ?eraDate . FILTER(YEAR(?eraDate) < 1990)\n', 30),
    ("2020s era", '  ?game wdt:P577 ?eraDate . FILTER(YEAR(?eraDate) >= 2020)\n', 30),
]
PLATFORM_SEARCH_TERMS: list[tuple[str, list[str], int]] = [
    ("xbox platform", ["Xbox"], 20),
    ("sega platform", ["Sega Genesis", "Sega Mega Drive", "Sega Saturn", "Sega Dreamcast", "Sega"], 20),
]
BROAD_SWEEP: tuple[str, str, int] = ("broad sweep", "", 220)

METADATA_QUERY_TEMPLATE = """# SavePoint bounded metadata enrichment, revision 1
SELECT ?game ?genreLabel ?platformLabel WHERE {
  VALUES ?game { %s }
  OPTIONAL { ?game wdt:P136 ?genre }
  OPTIONAL { ?game wdt:P400 ?platform }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    ?genre rdfs:label ?genreLabel .
    ?platform rdfs:label ?platformLabel .
  }
}
ORDER BY ?game ?genreLabel ?platformLabel
"""


class SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.redirects += 1
        _validate_url(newurl)
        if self.redirects > MAX_REDIRECTS:
            raise ValueError("Too many redirects from approved source")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Refusing non-allowlisted URL: {parsed.scheme}://{parsed.hostname}")
    if parsed.username or parsed.password:
        raise ValueError("Credentials are forbidden in acquisition URLs")


def _fetch_json(url: str, params: dict[str, str]) -> dict[str, Any]:
    _validate_url(url)
    full_url = f"{url}?{urlencode(params)}"
    request = Request(full_url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    opener = build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"application/json", "application/sparql-results+json"}:
                raise ValueError(f"Unexpected content type: {content_type}")
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ValueError("Approved source response exceeds size limit")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Acquisition failed without promoting candidate: {type(exc).__name__}") from exc
    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("External response must be a JSON object")
    return decoded


def _binding_value(binding: dict[str, Any], name: str) -> str | None:
    value = binding.get(name, {}).get("value")
    return value if isinstance(value, str) and value else None


def _qid(uri: str) -> str:
    match = re.fullmatch(r"https?://www\.wikidata\.org/entity/(Q\d+)", uri)
    if not match:
        raise ValueError("Wikidata entity URI is not canonical")
    return match.group(1)


def _image_title(uri: str) -> str | None:
    parsed = urlparse(uri)
    if parsed.hostname not in {"commons.wikimedia.org", "www.wikidata.org"}:
        return None
    marker = "/wiki/Special:FilePath/"
    if marker not in parsed.path:
        return None
    # urlparse does not decode percent-escapes (e.g. "%27" for an apostrophe) --
    # without unquoting, titles like "Assassin's Creed" survive as "Assassin%27s
    # Creed" and never match a real Commons page, so every lookup below silently
    # falls back to placeholder regardless of the file's actual licence.
    raw_name = unquote(parsed.path.split(marker, 1)[1])
    return "File:" + raw_name.replace("_", " ")


def _year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^(-?\d{4})", value)
    return int(match.group(1)) if match else None


def _era(year: int | None) -> str:
    if year is None:
        return "unknown"
    if year < 1990:
        return "pre-1990"
    if year < 2000:
        return "1990s"
    if year < 2010:
        return "2000s"
    if year < 2020:
        return "2010s"
    return "2020s"


def _platform_families(platforms: list[str]) -> list[str]:
    text = " ".join(platforms).casefold()
    families: list[str] = []
    rules = {
        "pc": ("windows", "linux", "macos", "computer", "dos"),
        "playstation": ("playstation",),
        "xbox": ("xbox",),
        "nintendo": ("nintendo", "game boy", "wii", "switch"),
        "sega": ("sega", "dreamcast", "mega drive", "genesis", "saturn"),
        "arcade-mobile-other": ("arcade", "android", "ios", "atari", "amiga", "commodore"),
    }
    for family, needles in rules.items():
        if any(needle in text for needle in needles):
            families.append(family)
    return families or ["other"]


def _aggregate(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    games: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        game_uri = _binding_value(binding, "game")
        en_label = _binding_value(binding, "enLabel")
        if not game_uri or not en_label:
            continue
        qid = _qid(game_uri)
        game = games.setdefault(
            qid,
            {
                "qid": qid,
                "titles": {"en": en_label, "es": _binding_value(binding, "esLabel")},
                "aliases": {"en": [], "es": []},
                "release_dates": set(),
                "genres": set(),
                "platforms": set(),
                "image_candidates": set(),
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
            },
        )
        for field, target in (("releaseDate", "release_dates"), ("genreLabel", "genres"), ("platformLabel", "platforms")):
            value = _binding_value(binding, field)
            if value:
                game[target].add(value)
        image_uri = _binding_value(binding, "image")
        if image_uri and (title := _image_title(image_uri)):
            game["image_candidates"].add(title)

    normalized: list[dict[str, Any]] = []
    for game in games.values():
        release_dates = sorted(game["release_dates"])
        platforms = sorted(game["platforms"], key=str.casefold)
        year = min((_year(item) for item in release_dates if _year(item) is not None), default=None)
        normalized.append(
            {
                **game,
                "release_dates": release_dates,
                "genres": sorted(game["genres"], key=str.casefold),
                "platforms": platforms,
                "image_candidates": sorted(game["image_candidates"], key=str.casefold),
                "coverage": {"era": _era(year), "platform_families": _platform_families(platforms)},
            }
        )
    # Truncate in insertion order first (coverage-critical sub-queries were merged
    # ahead of the broad sweep in `_run_acquisition_queries`, so they survive this
    # cut even if the broad sweep alone would exceed TARGET_COUNT), THEN sort the
    # retained subset by QID for deterministic, reproducible output ordering.
    selected = normalized[:TARGET_COUNT]
    return sorted(selected, key=lambda item: int(item["qid"][1:]))


def _enrich_bindings(base_bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identity: dict[str, dict[str, str | None]] = {}
    for binding in base_bindings:
        game_uri = _binding_value(binding, "game")
        if game_uri:
            identity[game_uri] = {
                "enLabel": _binding_value(binding, "enLabel"),
                "esLabel": _binding_value(binding, "esLabel"),
            }
    enriched = list(base_bindings)
    uris = sorted(identity, key=lambda uri: int(uri.rsplit("/Q", 1)[1]))
    for offset in range(0, len(uris), 40):
        query = METADATA_QUERY_TEMPLATE % " ".join(f"wd:{uri.rsplit('/', 1)[1]}" for uri in uris[offset : offset + 40])
        response = _fetch_json(WIKIDATA_ENDPOINT, {"query": query, "format": "json"})
        for binding in response.get("results", {}).get("bindings", []):
            if not isinstance(binding, dict):
                continue
            game_uri = _binding_value(binding, "game")
            values = identity.get(game_uri or "")
            if not values:
                continue
            for field in ("enLabel", "esLabel"):
                if values.get(field):
                    binding[field] = {"type": "literal", "value": values[field]}
            enriched.append(binding)
    return enriched


def _commons_metadata(titles: list[str]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(titles), 25):
        batch = titles[offset : offset + 25]
        response = _fetch_json(
            COMMONS_API,
            {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "prop": "imageinfo",
                "iiprop": "url|extmetadata",
                "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|Credit|UsageTerms",
                "titles": "|".join(batch),
            },
        )
        for page in response.get("query", {}).get("pages", []):
            if not isinstance(page, dict) or page.get("missing"):
                continue
            info = (page.get("imageinfo") or [{}])[0]
            ext = info.get("extmetadata") or {}
            clean = lambda key: html.unescape(re.sub(r"<[^>]+>", "", ext.get(key, {}).get("value", ""))).strip()
            results[page.get("title", "")] = {
                "author": clean("Artist"),
                "license": clean("LicenseShortName") or clean("UsageTerms"),
                "license_url": ext.get("LicenseUrl", {}).get("value", ""),
                "source_url": info.get("descriptionurl", ""),
                "file_url": info.get("url", ""),
                "credit": clean("Credit"),
            }
    return results


def _coverage(games: list[dict[str, Any]]) -> dict[str, Any]:
    eras: dict[str, int] = defaultdict(int)
    families: dict[str, int] = defaultdict(int)
    genres: set[str] = set()
    bilingual = 0
    for game in games:
        eras[game["coverage"]["era"]] += 1
        for family in game["coverage"]["platform_families"]:
            families[family] += 1
        genres.update(game["genres"])
        bilingual += int(bool(game["titles"].get("es")))
    return {
        "eras": dict(sorted(eras.items())),
        "platform_families": dict(sorted(families.items())),
        "distinct_genres": len(genres),
        "bilingual_title_count": bilingual,
    }


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def _validate_candidate(raw: dict[str, Any], catalogue: dict[str, Any], assets: dict[str, Any]) -> None:
    games = raw.get("games", [])
    if not MIN_COUNT <= len(games) <= MAX_COUNT:
        raise ValueError(f"Candidate count must be {MIN_COUNT}-{MAX_COUNT}, got {len(games)}")
    if len({game["qid"] for game in games}) != len(games):
        raise ValueError("Duplicate QID in candidate")
    coverage = catalogue.get("coverage", {})
    required_eras = {"pre-1990", "1990s", "2000s", "2010s", "2020s"}
    if not required_eras.issubset(coverage.get("eras", {})):
        raise ValueError("Candidate does not cover every required era")
    required_families = {"pc", "playstation", "xbox", "nintendo", "sega"}
    if not required_families.issubset(coverage.get("platform_families", {})):
        raise ValueError("Candidate does not cover required platform families")
    if coverage.get("distinct_genres", 0) < 8:
        raise ValueError("Candidate genre coverage is too narrow")
    raw_hash = _sha256(_canonical_bytes(raw))
    if catalogue.get("snapshot", {}).get("sha256") != raw_hash:
        raise ValueError("Catalogue manifest checksum mismatch")
    if assets.get("catalogue_sha256") != raw_hash:
        raise ValueError("Asset manifest is not linked to this catalogue snapshot")
    for asset in assets.get("assets", []):
        if asset.get("display_allowed") is not False or asset.get("review_status") != "pending-human-review":
            raise ValueError("External asset was approved without the human freeze gate")
        if not all(asset.get(key) for key in ("author", "license", "license_url", "source_url")):
            if asset.get("decision") != "placeholder":
                raise ValueError("Incomplete asset metadata must resolve to placeholder")


def _run_acquisition_queries() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Run each bounded sub-query and merge bindings, deduplicated by QID.

    Multiple sub-queries can return the same game (e.g. a 2020s Xbox title
    appears in both the era and platform queries); the first occurrence wins
    so later queries only contribute genuinely new candidates.
    """
    platform_queries = [
        built
        for label, terms, limit in PLATFORM_SEARCH_TERMS
        if (built := _build_platform_query(label, terms, limit)) is not None
    ]
    queries = [*STATIC_ACQUISITION_QUERIES, *platform_queries, BROAD_SWEEP]

    merged: dict[str, dict[str, Any]] = {}
    executed: list[dict[str, str]] = []
    for label, extra, limit in queries:
        query_text = _BASE_TEMPLATE.format(label=label, extra=extra, limit=limit)
        response = None
        last_exc: RuntimeError | None = None
        for attempt, backoff in enumerate((0, 5, 20), start=1):
            if backoff:
                time.sleep(backoff)
            try:
                response = _fetch_json(WIKIDATA_ENDPOINT, {"query": query_text, "format": "json"})
                break
            except RuntimeError as exc:
                # Public WDQS is a shared, occasionally slow/rate-limited endpoint;
                # conservative retries absorb transient timeouts without masking a
                # genuinely broken query (all attempts failing still raises).
                last_exc = exc
                print(f"  query '{label}': attempt {attempt} failed ({exc}), retrying...")
        if response is None:
            assert last_exc is not None
            raise last_exc
        bindings = response.get("results", {}).get("bindings")
        if not isinstance(bindings, list):
            raise ValueError(f"Wikidata response for '{label}' query has no bindings")
        executed.append({"label": label, "query": query_text, "row_count": str(len(bindings))})
        new_count = 0
        for binding in bindings:
            game_uri = _binding_value(binding, "game")
            if game_uri and game_uri not in merged:
                merged[game_uri] = binding
                new_count += 1
        print(f"  query '{label}': {len(bindings)} rows, {new_count} new games")
    return list(merged.values()), executed


def acquire() -> None:
    bindings, executed_queries = _run_acquisition_queries()
    games = _aggregate(_enrich_bindings(bindings))
    coverage = _coverage(games)
    raw = {
        "schema_version": 1,
        "status": "candidate-not-approved",
        "retrieved_at": RETRIEVED_AT,
        "source": "Wikidata Query Service",
        "source_url": WIKIDATA_ENDPOINT,
        "source_license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "query_revision": "savepoint-phase-01-v4",
        "queries": executed_queries,
        "metadata_query_template": METADATA_QUERY_TEMPLATE,
        "games": games,
    }
    raw_bytes = _canonical_bytes(raw)
    raw_hash = _sha256(raw_bytes)

    image_owners: dict[str, list[str]] = defaultdict(list)
    for game in games:
        for title in game["image_candidates"][:1]:
            image_owners[title].append(game["qid"])
    commons = _commons_metadata(sorted(image_owners, key=str.casefold)) if image_owners else {}
    asset_rows = []
    for title in sorted(image_owners, key=str.casefold):
        metadata = commons.get(title, {})
        complete = all(metadata.get(key) for key in ("author", "license", "license_url", "source_url"))
        asset_rows.append(
            {
                "asset_id": f"commons:{title}",
                "game_qids": sorted(image_owners[title]),
                "title": title,
                **metadata,
                "decision": "candidate" if complete else "placeholder",
                "review_status": "pending-human-review",
                "display_allowed": False,
                "fallback": "first-party-placeholder",
            }
        )

    catalogue = {
        "schema_version": 1,
        "status": "candidate-not-approved",
        "source": "Wikidata structured data",
        "source_url": "https://www.wikidata.org/",
        "license": "CC0 1.0",
        "license_url": "https://www.wikidata.org/wiki/Wikidata:Licensing",
        "retrieved_at": RETRIEVED_AT,
        "cutoff": RETRIEVED_AT,
        "query_revision": "savepoint-phase-01-v4",
        "query_sha256": _sha256(
            (json.dumps([q["query"] for q in raw["queries"]]) + METADATA_QUERY_TEMPLATE).encode("utf-8")
        ),
        "record_count": len(games),
        "coverage": coverage,
        "snapshot": {"path": "data/raw/wikidata-games.json", "sha256": raw_hash},
        "runtime_network_dependency": False,
        "promotion": "blocked-until-human-freeze",
    }
    assets = {
        "schema_version": 1,
        "status": "candidate-not-approved",
        "catalogue_sha256": raw_hash,
        "commons_policy_url": "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en",
        "retrieved_at": RETRIEVED_AT,
        "default_decision": "first-party-placeholder",
        "assets": asset_rows,
    }
    _validate_candidate(raw, catalogue, assets)
    _atomic_write(RAW_PATH, raw_bytes)
    _atomic_write(CATALOGUE_MANIFEST, _canonical_bytes(catalogue))
    _atomic_write(ASSET_MANIFEST, _canonical_bytes(assets))
    print(f"Candidate written: {len(games)} games, {len(asset_rows)} asset candidates, sha256={raw_hash}")


def validate_existing() -> None:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    catalogue = json.loads(CATALOGUE_MANIFEST.read_text(encoding="utf-8"))
    assets = json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))
    _validate_candidate(raw, catalogue, assets)
    print(f"Candidate valid and still unapproved: {catalogue['record_count']} games")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true", help="Validate checked-in candidates without network")
    args = parser.parse_args()
    validate_existing() if args.validate_only else acquire()


if __name__ == "__main__":
    main()
