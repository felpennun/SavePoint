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
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.serializers import build_public_profile

User = get_user_model()

# Uniform message for any invalid-credential outcome -- never reveal whether
# the username exists.
INVALID_CREDENTIALS_MESSAGE = "Invalid username or password."

# Registration outcome messages. Kept generic -- the client maps each HTTP
# status to its own localized copy row; these strings are only a fallback.
REGISTRATION_INVALID_MESSAGE = "Enter a username and a password."
REGISTRATION_WEAK_PASSWORD_MESSAGE = "Choose a stronger password and try again."
REGISTRATION_DUPLICATE_MESSAGE = "That username is already taken."

# Django's built-in User.username max_length.
USERNAME_MAX_LENGTH = 150


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
        # Mirror RegisterView: a crafted JSON body can make these a dict/list,
        # which slips past the truthiness guard and can raise deep in the auth
        # backend (500 instead of a clean 401).
        if not isinstance(username, str) or not isinstance(password, str):
            return Response({"detail": INVALID_CREDENTIALS_MESSAGE}, status=401)
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


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    """Controlled-demo self-registration (AUTH-02, D-08).

    D-08's middle path: a genuinely functional account-creation flow that
    still lives entirely inside the controlled academic demo boundary. A
    created account is a real, active user with a hashed password and an
    immediate logged-in session -- but it is *not* a simulated account
    (the ``DemoAccountIdentity`` marker is stamped only by the seed-time
    ``bootstrap_demo_accounts`` command, never here).

    Explicitly excluded: email verification, social auth, and any widening
    of the deployment's scope beyond the controlled demo it already is.

    Mirrors ``LoginView``: DRF's ``APIView`` is csrf_exempt at the Django
    middleware layer, so ``csrf_protect`` is re-applied here to enforce the
    get-cookie-then-post-token flow for this anonymous endpoint. A scoped
    per-IP anonymous throttle blunts automated abuse -- a throttled request
    is rejected before any user is created.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "registration"

    def post(self, request: Request) -> Response:
        username = request.data.get("username")
        password = request.data.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            return Response({"detail": REGISTRATION_INVALID_MESSAGE}, status=400)

        username = username.strip()
        if not username or not password:
            return Response({"detail": REGISTRATION_INVALID_MESSAGE}, status=400)
        if len(username) > USERNAME_MAX_LENGTH:
            return Response({"detail": REGISTRATION_INVALID_MESSAGE}, status=400)

        # Case-insensitive so near-duplicate aliases ("Alice" vs "alice")
        # can't both exist and confuse the demo.
        if User.objects.filter(username__iexact=username).exists():
            return Response({"detail": REGISTRATION_DUPLICATE_MESSAGE}, status=409)

        # Django's configured AUTH_PASSWORD_VALIDATORS (length, common,
        # numeric, similarity-to-username).
        try:
            validate_password(password, user=User(username=username))
        except DjangoValidationError:
            return Response({"detail": REGISTRATION_WEAK_PASSWORD_MESSAGE}, status=400)

        try:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password)
        except IntegrityError:
            # Lost a race against a concurrent identical registration.
            return Response({"detail": REGISTRATION_DUPLICATE_MESSAGE}, status=409)

        # Log the new session in via the same mechanism LoginView uses;
        # Django rotates the session key here to prevent fixation.
        login(request, user)

        # D-03: a freshly registered visitor lands on the catalogue. The
        # client owns the locale prefix, so this stays a bare relative path.
        return Response({"detail": "ok", "next": "/catalogue"}, status=201)


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
