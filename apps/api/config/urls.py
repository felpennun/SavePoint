"""Root URL configuration; feature routes are added by downstream plans."""

import os

from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    # Render supplies RENDER_GIT_COMMIT at runtime. Exposing the non-secret
    # revision lets the deployment smoke prove it reached the intended image,
    # rather than a stale healthy instance. Local runs remain identifiable.
    return JsonResponse({"status": "ok", "commit": os.environ.get("RENDER_GIT_COMMIT", "local")})


urlpatterns = [
    path("health/", health, name="health"),
    path("api/catalogue/", include("catalogue.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/library/", include("library.urls")),
]
