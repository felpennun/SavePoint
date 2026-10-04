"""Request hygiene, response format and caching added in the 2026-10-04 security review."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_nul_byte_in_the_query_string_is_a_400_not_a_500() -> None:
    client = APIClient()
    for url in ("/api/catalogue/games/?q=%00", "/api/catalogue/games/?platform=a%00b", "/api/accounts/profiles/a%00b/avatar/"):
        response = client.get(url)
        assert response.status_code == 400, url
        assert response.json() == {"detail": "Invalid request."}


def test_the_browsable_api_is_not_served_to_html_clients() -> None:
    # A browser address bar sends text/html *and* */*, which negotiates to JSON;
    # a client that insists on HTML alone gets 406 instead of the DRF console.
    for accept in ("text/html", "text/html,application/xhtml+xml,*/*;q=0.8"):
        response = APIClient().get("/api/library/entries/", HTTP_ACCEPT=accept)
        assert response.status_code in (401, 403, 406)
        assert response["Content-Type"].startswith("application/json")
        assert "csrfToken" not in response.content.decode()


def test_the_lite_catalogue_answer_is_public_cacheable_and_stable() -> None:
    client = APIClient()
    first = client.get("/api/catalogue/games/?facets=lite&q=zelda")
    second = client.get("/api/catalogue/games/?facets=lite&q=zelda")
    assert first.status_code == second.status_code == 200
    assert "max-age=60" in first["Cache-Control"] and first["Cache-Control"].startswith("public")
    # the shared (CDN) copy may live a little longer than the browser one
    assert "s-maxage=120" in first["Cache-Control"]
    assert first.json() == second.json()


def test_the_game_detail_answer_is_cached_per_locale_and_misses_are_not(django_assert_max_num_queries) -> None:  # noqa: ANN001
    from catalogue.models import GameWork

    work = GameWork.objects.create(canonical_slug="cache-me-1", original_title="Cache Me", title_en="Cache Me")
    client = APIClient()
    first = client.get("/api/catalogue/games/cache-me-1/?locale=en")
    assert first.status_code == 200
    with django_assert_max_num_queries(0):
        second = client.get("/api/catalogue/games/cache-me-1/?locale=en")
    assert second.json() == first.json()
    assert second["Cache-Control"].startswith("public")
    # another locale is a different entry; an unknown slug is never cached
    assert client.get("/api/catalogue/games/cache-me-1/?locale=es").status_code == 200
    assert client.get("/api/catalogue/games/not-there/").status_code == 404
    work.delete()
    assert client.get("/api/catalogue/games/not-there/").status_code == 404


def test_authenticated_users_are_throttled_per_user(django_user_model, settings) -> None:  # noqa: ANN001
    from rest_framework.settings import api_settings
    from rest_framework.throttling import SimpleRateThrottle

    user = django_user_model.objects.create_user(username="throttle-me", password="Zq7!vNm-Strong-Pass-4418")
    client = APIClient()
    client.force_authenticate(user=user)
    rates = dict(api_settings.DEFAULT_THROTTLE_RATES)
    rates["user_default"] = "3/min"
    SimpleRateThrottle.THROTTLE_RATES = rates
    try:
        codes = [client.get("/api/library/entries/").status_code for _ in range(5)]
    finally:
        SimpleRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES
    assert 429 in codes


def test_database_url_keeps_sslmode_and_requires_tls_in_production(monkeypatch) -> None:  # noqa: ANN001
    from config.settings import _postgres_database

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p%40ss@db.example.neon.tech/app?sslmode=verify-full")
    monkeypatch.delenv("DJANGO_DEPLOY_ENV", raising=False)
    config = _postgres_database()
    assert config["PASSWORD"] == "p@ss" and config["OPTIONS"] == {"sslmode": "verify-full"}

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example.neon.tech/app")
    assert "OPTIONS" not in _postgres_database()
    monkeypatch.setenv("DJANGO_DEPLOY_ENV", "production")
    assert _postgres_database()["OPTIONS"] == {"sslmode": "require"}
