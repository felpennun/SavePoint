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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
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
TIMEOUT_SECONDS = 60
MAX_REDIRECTS = 2
TARGET_COUNT = 150
MIN_COUNT = 100
MAX_COUNT = 300
RETRIEVED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# revision 3: removed wikibase:sitelinks join (caused consistent 30 s timeout on the
# public SPARQL endpoint). Now uses a curated VALUES list of well-known QIDs spanning
# multiple eras/genres/platforms (D-05/D-06), with OPTIONAL metadata blocks.
# The QID list is the reproducible selection artefact; it can be extended without
# changing the query structure.
_CURATED_QIDS = """
  wd:Q170325 wd:Q171044 wd:Q208185 wd:Q242700 wd:Q188195
  wd:Q208743 wd:Q210073 wd:Q171573 wd:Q272188 wd:Q208400
  wd:Q166542 wd:Q168975 wd:Q171282 wd:Q171897 wd:Q170434
  wd:Q16938 wd:Q49100 wd:Q83404 wd:Q110391 wd:Q201735
  wd:Q614807 wd:Q523792 wd:Q80165 wd:Q848512 wd:Q726267
  wd:Q9371 wd:Q1361394 wd:Q1361396 wd:Q223974 wd:Q742376
  wd:Q204406 wd:Q209163 wd:Q226602 wd:Q498383 wd:Q180079
  wd:Q287513 wd:Q4945 wd:Q40447 wd:Q246994 wd:Q309588
  wd:Q193581 wd:Q201705 wd:Q184537 wd:Q1361372 wd:Q1361378
  wd:Q271455 wd:Q325580 wd:Q1361357 wd:Q1361363 wd:Q183069
  wd:Q234808 wd:Q243951 wd:Q173013 wd:Q275535 wd:Q254654
  wd:Q167726 wd:Q163010 wd:Q154706 wd:Q131219 wd:Q124592
  wd:Q369822 wd:Q208159 wd:Q208309 wd:Q172881 wd:Q208085
  wd:Q207786 wd:Q209293 wd:Q214964 wd:Q163016 wd:Q220783
  wd:Q250256 wd:Q274053 wd:Q317537 wd:Q338017 wd:Q366516
  wd:Q381861 wd:Q388380 wd:Q389567 wd:Q397895 wd:Q402815
  wd:Q407484 wd:Q419049 wd:Q426778 wd:Q430742 wd:Q452484
  wd:Q454052 wd:Q456810 wd:Q459447 wd:Q464218 wd:Q473800
  wd:Q476553 wd:Q480180 wd:Q487929 wd:Q490920 wd:Q496658
  wd:Q500438 wd:Q501218 wd:Q504977 wd:Q506426 wd:Q515183
  wd:Q519776 wd:Q524140 wd:Q527398 wd:Q533266 wd:Q538555
  wd:Q543264 wd:Q548289 wd:Q556574 wd:Q563374 wd:Q571609
  wd:Q577706 wd:Q581401 wd:Q584534 wd:Q589113 wd:Q595185
  wd:Q601013 wd:Q607052 wd:Q617073 wd:Q622440 wd:Q628272
  wd:Q634564 wd:Q641378 wd:Q648393 wd:Q651978 wd:Q655332
  wd:Q659561 wd:Q663448 wd:Q667337 wd:Q671224 wd:Q675113
  wd:Q679002 wd:Q682891 wd:Q686780 wd:Q690669 wd:Q694558
  wd:Q698447 wd:Q702336 wd:Q706225 wd:Q710114 wd:Q714003
  wd:Q717892 wd:Q721781 wd:Q725670 wd:Q729559 wd:Q733448
  wd:Q737337 wd:Q741226 wd:Q745115 wd:Q749004 wd:Q752893
"""

QUERY = """# SavePoint Phase 1 candidate query, revision 3 (2026-09-04)
# Uses a curated VALUES list to avoid the expensive wikibase:sitelinks join.
SELECT ?game ?enLabel ?esLabel (MIN(?date) AS ?releaseDate)
       (SAMPLE(?candidateImage) AS ?image) WHERE {{
  VALUES ?game {{ {qids} }}
  ?game rdfs:label ?enLabel . FILTER(LANG(?enLabel) = "en")
  OPTIONAL {{ ?game rdfs:label ?esLabel . FILTER(LANG(?esLabel) = "es") }}
  OPTIONAL {{ ?game wdt:P577 ?date }}
  OPTIONAL {{ ?game wdt:P18 ?candidateImage }}
}}
GROUP BY ?game ?enLabel ?esLabel
ORDER BY ?game
""".format(qids=_CURATED_QIDS)

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
    return "File:" + parsed.path.split(marker, 1)[1].replace("_", " ")


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
    return sorted(normalized, key=lambda item: int(item["qid"][1:]))[:TARGET_COUNT]


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


def acquire() -> None:
    response = _fetch_json(WIKIDATA_ENDPOINT, {"query": QUERY, "format": "json"})
    bindings = response.get("results", {}).get("bindings")
    if not isinstance(bindings, list):
        raise ValueError("Wikidata response has no bindings")
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
        "query_revision": "savepoint-phase-01-v2",
        "query": QUERY,
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
        "query_revision": "savepoint-phase-01-v2",
        "query_sha256": _sha256((QUERY + METADATA_QUERY_TEMPLATE).encode("utf-8")),
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
