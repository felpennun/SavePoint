"""Bounded-page IGDB v4 API client (Plan 01.1-02, ADR-006).

Offline use only: this is called exclusively by the ``import_igdb_catalogue``
management command, never on a request path (CAT-06 / OPS-03).

Security contract (threat T-01.1-02, Information Disclosure):
- ``IGDB_CLIENT_ID`` / ``IGDB_CLIENT_SECRET`` are read from the process
  environment by name. Their values, the OAuth bearer token, and every
  ``Authorization`` / ``Client-ID`` header are NEVER returned, logged, or
  placed in an exception message.
- Every string that could reach a log, a raised exception, or the freeze
  evidence is passed through :func:`redact` first. Chained exception context
  from ``requests`` is dropped (``raise ... from None``) because it can carry
  the outbound URL with credentials in the query string.

Throttling (probe evidence ``docs/verification/igdb-api-probe.md`` §4):
4 req/s + 8 concurrent, no monthly quota, no rate-limit headers -- a 429
body is the only signal, so ret/backoff is 429/5xx-aware with a hard cap.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Iterator

import requests

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
GAMES_URL = "https://api.igdb.com/v4/games"
GAMES_COUNT_URL = "https://api.igdb.com/v4/games/count"

# Apicalypse field list -- dot expansion keeps genres/platforms/cover to a
# single request per page (ADR-006 anti-pattern: no N+1 per-game lookups).
GAME_FIELDS = (
    "id,name,slug,url,first_release_date,total_rating,"
    "genres.id,genres.name,platforms.id,platforms.name,cover.image_id"
)

DEFAULT_TIMEOUT = (10, 45)          # (connect, read) seconds
MIN_REQUEST_INTERVAL = 0.30        # ~3.3 req/s, safely under the documented 4 req/s
MAX_RETRIES = 5
BACKOFF_BASE = 1.0
BACKOFF_CAP = 60.0

_SECRET_PATTERNS = (
    re.compile(r"(client_secret=)[^&\s\"']+", re.IGNORECASE),
    re.compile(r"(client_id=)[^&\s\"']+", re.IGNORECASE),
    re.compile(r"(access_token\"?\s*[:=]\s*\"?)[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE),
)


def redact(text: str) -> str:
    """Scrub credential-shaped substrings from any outbound text."""
    scrubbed = str(text)
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub(r"\1***", scrubbed)
    return scrubbed


class IgdbClientError(RuntimeError):
    """Raised for any IGDB access failure. The message is redacted on
    construction so callers can safely log or re-raise it."""

    def __init__(self, message: object) -> None:
        super().__init__(redact(str(message)))


class IgdbClient:
    """Fetches pages of IGDB primary games with id-cursor pagination."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client_id = client_id or os.environ.get("IGDB_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("IGDB_CLIENT_SECRET")
        if not self._client_id or not self._client_secret:
            raise IgdbClientError(
                "IGDB_CLIENT_ID and IGDB_CLIENT_SECRET must be set in the environment"
            )
        self._session = session or requests.Session()
        self._sleep = sleep
        self._token: str | None = None
        self._token_expiry = 0.0
        self._last_request_at = 0.0

    # -- redaction ---------------------------------------------------------

    def _scrub(self, text: object) -> str:
        out = str(text)
        for literal in (self._client_id, self._client_secret, self._token):
            if literal:
                out = out.replace(literal, "***")
        return redact(out)

    # -- pacing ----------------------------------------------------------

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = MIN_REQUEST_INTERVAL - elapsed
        if wait > 0:
            self._sleep(wait)
        self._last_request_at = time.monotonic()

    def _backoff(self, attempt: int) -> None:
        self._sleep(min(BACKOFF_CAP, BACKOFF_BASE * (2 ** (attempt - 1))))

    # -- auth ----------------------------------------------------------

    def _token_value(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        try:
            resp = self._session.post(
                TOKEN_URL,
                params={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "grant_type": "client_credentials",
                },
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise IgdbClientError(f"token request failed: {self._scrub(exc)}") from None
        if resp.status_code != 200:
            raise IgdbClientError(f"token endpoint returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            self._token = str(data["access_token"])
        except (ValueError, KeyError, TypeError) as exc:
            raise IgdbClientError(f"token response was not usable: {self._scrub(exc)}") from None
        self._token_expiry = time.time() + int(data.get("expires_in", 0))
        return self._token

    # -- requests ----------------------------------------------------------

    def _post(self, url: str, body: str) -> requests.Response:
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            token = self._token_value()
            headers = {
                "Client-ID": self._client_id,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
            try:
                resp = self._session.post(
                    url, data=body.encode("utf-8"), headers=headers, timeout=DEFAULT_TIMEOUT
                )
            except requests.RequestException as exc:
                if attempt == MAX_RETRIES:
                    raise IgdbClientError(
                        f"{url} failed after {attempt} attempts: {self._scrub(exc)}"
                    ) from None
                self._backoff(attempt)
                continue

            if resp.status_code == 401:
                self._token = None
                if attempt == MAX_RETRIES:
                    raise IgdbClientError(f"{url} still unauthorized after token refresh")
                continue
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise IgdbClientError(
                        f"{url} returned HTTP {resp.status_code} after {attempt} attempts"
                    )
                self._backoff(attempt)
                continue
            if resp.status_code != 200:
                raise IgdbClientError(
                    f"{url} returned HTTP {resp.status_code}: {self._scrub(resp.text[:300])}"
                )
            return resp
        raise IgdbClientError(f"{url} exhausted {MAX_RETRIES} retries")

    # -- public API ----------------------------------------------------------

    def count_eligible(self, where: str = "game_type = 0") -> int:
        """Live re-measurement of the eligible primary-game count."""
        resp = self._post(GAMES_COUNT_URL, f"where {where};")
        try:
            return int(resp.json()["count"])
        except (ValueError, KeyError, TypeError) as exc:
            raise IgdbClientError(f"count response was not usable: {self._scrub(exc)}") from None

    def fetch_page(
        self, after_id: int, page_size: int = 500, where: str = "game_type = 0"
    ) -> list[dict]:
        """One id-cursored page: ``where <where> & id > after_id; sort id asc``."""
        body = (
            f"fields {GAME_FIELDS}; "
            f"where {where} & id > {int(after_id)}; "
            f"sort id asc; limit {int(page_size)};"
        )
        resp = self._post(GAMES_URL, body)
        try:
            rows = resp.json()
        except ValueError as exc:
            raise IgdbClientError(f"games response was not JSON: {self._scrub(exc)}") from None
        if not isinstance(rows, list):
            raise IgdbClientError("games response was not a JSON array")
        return rows

    def iter_pages(
        self, after_id: int = 0, page_size: int = 500, where: str = "game_type = 0"
    ) -> Iterator[list[dict]]:
        cursor = int(after_id)
        while True:
            rows = self.fetch_page(cursor, page_size=page_size, where=where)
            if not rows:
                return
            yield rows
            cursor = int(rows[-1]["id"])
