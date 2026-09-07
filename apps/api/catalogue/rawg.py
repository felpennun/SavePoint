"""Bounded RAWG API client for offline rating enrichment.

The client is deliberately narrower than the IGDB client: it only searches
the fixed RAWG games endpoint and never runs on a request path. API keys stay
in the process environment and are never included in errors or evidence.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

import requests

RAWG_GAMES_URL = "https://api.rawg.io/api/games"
RAWG_TERMS_URL = "https://rawg.io/apidocs"
RAWG_LICENCE = "RAWG Free API terms (non-commercial, attribution and backlink required)"
DEFAULT_TIMEOUT = (10, 45)
MAX_RETRIES = 5
BACKOFF_BASE = 1.0
BACKOFF_CAP = 60.0


class RawgClientError(RuntimeError):
    """Raised for a RAWG access or response-shape failure."""


class RawgClient:
    """Fetch exact-title search candidates from the fixed RAWG host."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key or os.environ.get("RAWG_API_KEY")
        if not self._api_key:
            raise RawgClientError("RAWG_API_KEY must be set in the environment")
        self._session = session or requests.Session()
        self._sleep = sleep

    def _get(self, params: dict[str, str | int]) -> dict:
        request_params = {"key": self._api_key, **params}
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._session.get(
                    RAWG_GAMES_URL,
                    params=request_params,
                    timeout=DEFAULT_TIMEOUT,
                    allow_redirects=False,
                )
            except requests.RequestException:
                if attempt == MAX_RETRIES:
                    raise RawgClientError(
                        f"{RAWG_GAMES_URL} failed after {attempt} attempts"
                    ) from None
                self._sleep(min(BACKOFF_CAP, BACKOFF_BASE * (2 ** (attempt - 1))))
                continue

            if 300 <= response.status_code < 400:
                raise RawgClientError(f"{RAWG_GAMES_URL} returned an unexpected redirect")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise RawgClientError(
                        f"{RAWG_GAMES_URL} returned HTTP {response.status_code} after {attempt} attempts"
                    )
                self._sleep(min(BACKOFF_CAP, BACKOFF_BASE * (2 ** (attempt - 1))))
                continue
            if response.status_code != 200:
                raise RawgClientError(f"{RAWG_GAMES_URL} returned HTTP {response.status_code}")
            try:
                payload = response.json()
            except (TypeError, ValueError) as exc:
                raise RawgClientError("RAWG response was not valid JSON") from None
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise RawgClientError("RAWG response did not contain a results list")
            return payload
        raise RawgClientError(f"{RAWG_GAMES_URL} exhausted {MAX_RETRIES} retries")

    def search_games(self, title: str, *, page_size: int = 40) -> list[dict]:
        """Return bounded exact-search candidates without following redirects."""

        payload = self._get(
            {
                "search": title,
                "search_exact": "true",
                "page_size": min(max(int(page_size), 1), 40),
            }
        )
        return [item for item in payload["results"] if isinstance(item, dict)]
