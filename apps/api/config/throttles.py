"""Throttles shared by the API.

``AuthenticatedUserThrottle`` is the default for every view that does not pick
its own scope: it only counts signed-in users (keyed by user id), so server-side
page renders for anonymous visitors -- which all arrive from the web tier's
address -- are never throttled by it. ``ProfileImageWriteThrottle`` limits only
the writes (PUT/DELETE) of the profile photo/cover endpoints.
"""

from __future__ import annotations

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class AuthenticatedUserThrottle(SimpleRateThrottle):
    scope = "user_default"

    def get_cache_key(self, request, view):  # noqa: ANN001
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": user.pk}


class ProfileImageWriteThrottle(ScopedRateThrottle):
    def allow_request(self, request, view):  # noqa: ANN001
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
