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

from accounts.serializers import (
    AccountProfileSerializer,
    ReplaceFavoritesRequestSerializer,
    build_public_profile,
    serialize_account_profile,
    serialize_capabilities,
    serialize_favorite_slots,
)
from accounts.services import get_or_create_profile, replace_favorites, update_profile

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
    # Blunt online password-guessing: the uniform error message defeats
    # username *enumeration* but not brute force. Scope + rate in settings.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

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
        if user is None:
            # Registration enforces case-insensitive username uniqueness
            # (``username__iexact``), but Django's ModelBackend matches the
            # username case-sensitively. Without this retry a visitor who
            # registered as "Alice" is locked out the instant they type
            # "alice": login rejects them and registration refuses to
            # recreate the account. Resolve to the stored spelling and try
            # once more. The uniform error below still hides whether the
            # username exists.
            canonical = (
                User.objects.filter(username__iexact=username)
                .exclude(username=username)
                .order_by("pk")
                .values_list("username", flat=True)
                .first()
            )
            if canonical:
                user = authenticate(request, username=canonical, password=password)
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
        except DjangoValidationError as exc:
            # Return the concrete validator messages (too short, too common,
            # entirely numeric, too similar to the username) so the client
            # can tell the visitor exactly what to fix instead of a vague
            # "weak password".
            return Response(
                {
                    "detail": REGISTRATION_WEAK_PASSWORD_MESSAGE,
                    "password_errors": list(exc.messages),
                },
                status=400,
            )

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


class MeView(APIView):
    """GET /api/accounts/me/ -- the signed-in visitor's own identity.

    The navbar account control and the home greeting read this to show
    *which* account is active. An anonymous caller gets 401 with no body,
    so a 200 always carries a username. Deliberately minimal: alias plus a
    demo/real flag, never email or internal IDs.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        is_demo = hasattr(user, "demo_identity") or hasattr(user, "demo_anchor")
        return Response(
            {
                "username": user.username,
                "is_demo": is_demo,
                "capabilities": serialize_capabilities(user),
            }
        )


class MyProfileView(APIView):
    """GET/PATCH /api/accounts/me/profile/ -- the signed-in owner's editable
    profile (PROF-01).

    The alias (``User.username``) is never accepted or returned here -- D-01
    keeps it immutable, and the owner is always ``request.user``: no
    identity is ever accepted from the request body (IDOR boundary).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        profile = get_or_create_profile(user=request.user)
        return Response(serialize_account_profile(profile))

    def patch(self, request: Request) -> Response:
        serializer = AccountProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"detail": "Invalid profile update.", "errors": serializer.errors}, status=400)

        try:
            profile = update_profile(user=request.user, **serializer.validated_data)
        except DjangoValidationError as exc:
            return Response({"detail": str(exc.message if hasattr(exc, "message") else exc)}, status=400)

        return Response(serialize_account_profile(profile))


class MyFavoritesView(APIView):
    """GET/PUT /api/accounts/me/favorites/ -- the signed-in owner's five
    favorite-shelf slots (D-02).

    PUT is a full replace: the submitted set is authoritative, matching the
    ``save_library_configuration`` pattern in ``library.services``. Every
    work must already belong to the caller's own collection -- the owner is
    always ``request.user``, never accepted from the payload (IDOR
    boundary).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response({"slots": serialize_favorite_slots(request.user)})

    def put(self, request: Request) -> Response:
        serializer = ReplaceFavoritesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid favorites payload.", "errors": serializer.errors}, status=400)

        try:
            replace_favorites(user=request.user, slots=serializer.validated_data["slots"])
        except DjangoValidationError as exc:
            return Response({"detail": str(exc.message if hasattr(exc, "message") else exc)}, status=400)

        return Response({"slots": serialize_favorite_slots(request.user)})


class PublicProfileView(APIView):
    """GET /api/accounts/profiles/<alias>/

    PROF-02/INV-05: an unauthorized or nonexistent alias returns the exact
    same 404 -- never reveal which case occurred. D-02/D-03 (Phase 5):
    ``collection_visibility``/``favorites_visibility`` are resolved inside
    ``build_public_profile`` before any private data is even queried; the
    owner viewing their own alias always sees their own full data, while
    every other caller (anonymous or a different account) gets the
    privacy-resolved projection. An account with no explicit privacy
    settings yet defaults to public, matching the pre-Phase-5 behavior.

    An anonymous scoped throttle blunts scripted alias enumeration -- a
    200-vs-404 still reveals existence, but not at scraping speed (M-03).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_profile"

    def get(self, request: Request, alias: str) -> Response:
        user = User.objects.filter(username=alias, is_active=True).first()
        if user is None:
            return Response({"detail": "Not found."}, status=404)
        profile = build_public_profile(user, viewer=request.user)
        if profile is None:
            return Response({"detail": "Not found."}, status=404)
        return Response(profile)
