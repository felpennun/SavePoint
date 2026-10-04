"""The home page figures endpoint."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from catalogue.views import CATALOGUE_STATS_CACHE_KEY


@pytest.mark.django_db
def test_stats_are_public_aggregates_with_the_expected_keys() -> None:
    cache.delete(CATALOGUE_STATS_CACHE_KEY)
    response = APIClient().get("/api/catalogue/stats/")
    assert response.status_code == 200
    assert set(response.json()) == {"games", "rated", "platforms", "first_year", "last_year"}
    assert response.json()["games"] >= response.json()["rated"] >= 0


@pytest.mark.django_db
def test_stats_are_served_from_the_cache_after_the_first_call() -> None:
    cache.set(CATALOGUE_STATS_CACHE_KEY, {"games": 7, "rated": 3, "platforms": 2, "first_year": 1990, "last_year": 2020}, 60)
    assert APIClient().get("/api/catalogue/stats/").json()["games"] == 7
    cache.delete(CATALOGUE_STATS_CACHE_KEY)


@pytest.mark.django_db
def test_lite_facets_skip_the_heavy_dimensions_and_are_cached() -> None:
    from catalogue.search import LITE_FACETS_CACHE_KEY

    cache.delete(LITE_FACETS_CACHE_KEY)
    client = APIClient()
    lite = client.get("/api/catalogue/games/", {"facets": "lite"}).json()["facets"]
    assert lite["developers"] == [] and lite["franchises"] == [] and lite["publishers"] == []
    assert lite["modes"] == [] and lite["editions"] == []
    assert {"platforms", "tags", "genres", "dates", "year_range"} <= set(lite)
    assert cache.get(LITE_FACETS_CACHE_KEY) is not None
    cache.delete(LITE_FACETS_CACHE_KEY)
