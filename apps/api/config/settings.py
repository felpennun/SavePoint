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
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "accounts.apps.AccountsConfig",
    "catalogue.apps.CatalogueConfig",
    "library.apps.LibraryConfig",
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

LANGUAGE_CODE = "es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
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
