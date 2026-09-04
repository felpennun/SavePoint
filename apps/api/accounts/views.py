"""Session auth endpoints (AUTH-01): conventional username/password, CSRF
enforced even pre-session, uniform invalid-credential response, logout
invalidates the session.

DRF's APIView marks itself csrf_exempt at the Django-middleware level and
only re-enforces CSRF inside SessionAuthentication once a user is already
authenticated -- an anonymous login POST would otherwise sail through with
no CSRF check at all. LoginView explicitly re-applies Django's own
csrf_protect so the classic get-cookie-then-post-token flow is enforced
here too.
"""

from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import build_public_profile

User = get_user_model()

# Uniform message for any invalid-credential outcome -- never reveal whether
# the username exists.
INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfBootstrapView(APIView):
    """GET this once before login to receive the CSRF cookie the POST needs."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"detail": "ok"})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"detail": INVALID_CREDENTIALS_MESSAGE}, status=401)

        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_active:
            return Response({"detail": INVALID_CREDENTIALS_MESSAGE}, status=401)

        login(request, user)

        # D-03: successful login always leads to the catalogue -- the only
        # honored redirect target is a same-origin relative path; anything
        # else (external host, protocol-relative //evil.com, scheme change)
        # is discarded in favor of the safe default.
        requested_next = request.data.get("next")
        safe_next = "/catalogue"
        if requested_next and url_has_allowed_host_and_scheme(
            url=requested_next, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            safe_next = requested_next

        return Response({"detail": "ok", "next": safe_next})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"detail": "ok"})


class PublicProfileView(APIView):
    """GET /api/accounts/profiles/<alias>/

    PROF-02/INV-05: an unauthorized or nonexistent alias returns the exact
    same 404 -- never reveal which case occurred. Phase 1 has no
    public/private toggle (a small controlled demo where every account is
    public by design; FLAGGED ASSUMPTION -- see plan 01-07), so today the
    only 404 case is "no such user", but the response is built to stay
    indistinguishable if a privacy toggle is added later.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request, alias: str) -> Response:
        user = User.objects.filter(username=alias, is_active=True).first()
        if user is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(build_public_profile(user))
