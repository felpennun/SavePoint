"""Base settings shared by local, test, and deployed SavePoint runtimes."""

from pathlib import Path
import os
from urllib.parse import unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]
if render_hostname := os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    # Provider-owned, non-user input: required because Render health checks
    # use the public service hostname in Host even though application traffic
    # from the web proxy arrives over the private network.
    ALLOWED_HOSTS.append(render_hostname)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "audit.apps.AuditConfig",
    "accounts.apps.AccountsConfig",
    "catalogue.apps.CatalogueConfig",
    "library.apps.LibraryConfig",
    "recommendations.apps.RecommendationsConfig",
    "evaluation.apps.EvaluationConfig",
    "social.apps.SocialConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def _postgres_database() -> dict[str, object]:
    """Parse only PostgreSQL URLs; unsupported engines fail closed."""
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        required = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError("Missing PostgreSQL configuration: " + ", ".join(missing))
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }

    parsed = urlparse(raw_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL must use the PostgreSQL scheme")
    if not all((parsed.hostname, parsed.path.removeprefix("/"), parsed.username)):
        raise RuntimeError("DATABASE_URL is missing required PostgreSQL connection fields")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.removeprefix("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 60,
    }


DATABASES = {"default": _postgres_database()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Authentication: pin DRF to SessionAuthentication only. DRF's unconfigured
# default also enables BasicAuthentication, which would (a) accept
# username/password on every request as an unthrottled online-guessing
# channel and (b) skip CSRF on state-changing endpoints -- a second door
# around the session/CSRF model the auth views deliberately enforce
# (repo-review-2026-09-06 H-01). Anonymous endpoints (login/register/csrf)
# still set `authentication_classes = []` locally.
#
# Throttling: DEFAULT_THROTTLE_CLASSES stays empty so throttling applies
# only to views that opt in. Scopes:
#   registration -- controlled-demo self-registration ceiling (AUTH-02/D-08,
#                   threat T-01.1-07)
#   login        -- blunts online password-guessing against LoginView (H-01/M-01)
#   public_profile -- blunts unauthenticated alias enumeration (M-03)
#   recommendations -- caps authenticated CPU/DB-heavy ranking runs
#   popularity      -- caps the public aggregate ranking endpoint
#   research        -- caps read-only publication-panel access
# ScopedRateThrottle keys on the client IP. Behind the deployed
# browser -> Vercel rewrite -> Render chain, REMOTE_ADDR is a single
# upstream address, so per-IP scoping only works if NUM_PROXIES matches the
# real hop count. It is read from DJANGO_NUM_PROXIES (default 0 = trust
# REMOTE_ADDR directly, correct for local/Docker); deploy MUST set it to the
# real chain length or the per-IP limits collapse to global (M-02).
_num_proxies_raw = os.environ.get("DJANGO_NUM_PROXIES", "").strip()
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "registration": "5/hour",
        "login": "10/min",
        "public_profile": "30/min",
        "recommendations": "30/min",
        "popularity": "60/min",
        # Generous enough for real catalogue browsing/typing; caps a scripted
        # `?q=<random>` loop that would otherwise drive an unauthenticated
        # trigram scan on every hit (M-05).
        "catalogue_search": "120/min",
        "social_search": "30/min",
        "social_mutation": "60/min",
        "research": "60/min",
    },
    # ``format`` belongs to the allowlisted research export query, not to
    # DRF's renderer override.  Keeping the override disabled also prevents
    # arbitrary format negotiation from bypassing endpoint validation.
    "URL_FORMAT_OVERRIDE": None,
    "NUM_PROXIES": int(_num_proxies_raw) if _num_proxies_raw.isdigit() else None,
}

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Fail-closed deploy profile (SEC-02/OPS-02): "local" is plain HTTP behind
# Docker Compose with no TLS terminator, so `manage.py check --deploy`'s
# HSTS/SSL-redirect/secure-cookie warnings are Django's own documented
# guidance for exactly that case (silenced, not fixed, since forcing HTTPS
# redirects here would break the working local demo). "production" instead
# requires those protections and a real, sufficiently long secret key --
# never a silent downgrade.
DJANGO_DEPLOY_ENV = os.environ.get("DJANGO_DEPLOY_ENV", "local")
if DJANGO_DEPLOY_ENV not in {"local", "production"}:
    raise RuntimeError("DJANGO_DEPLOY_ENV must be 'local' or 'production'")

if DJANGO_DEPLOY_ENV == "production":
    if len(SECRET_KEY) < 50:
        raise RuntimeError("DJANGO_SECRET_KEY must be at least 50 characters when DJANGO_DEPLOY_ENV=production")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Render terminates public TLS before forwarding to the container. Trust
    # only its conventional proxy-proto header so SECURE_SSL_REDIRECT and
    # Django's CSRF secure-origin checks do not loop on internal HTTP.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SILENCED_SYSTEM_CHECKS: list[str] = []
else:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SECURE_COOKIES", "false").lower() == "true"
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SILENCED_SYSTEM_CHECKS = [
        "security.W004",  # SECURE_HSTS_SECONDS -- no TLS terminator locally
        "security.W008",  # SECURE_SSL_REDIRECT -- plain HTTP locally
        "security.W012",  # SESSION_COOKIE_SECURE -- plain HTTP locally
        "security.W016",  # CSRF_COOKIE_SECURE -- plain HTTP locally
    ]
