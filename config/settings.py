"""Django settings for the Pi dashboard.

Every deployment-specific value comes from environment variables or a ``.env``
file next to ``manage.py``. Nothing secret lives in this file.
"""

import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
if not env.bool("PIDASH_SKIP_DOTENV", default=False):
    environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("PIDASH_DEBUG", default=False)

SECRET_KEY = env("PIDASH_SECRET_KEY", default="")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set PIDASH_SECRET_KEY (see .env.example).")
    SECRET_KEY = "insecure-development-key-do-not-use-in-production"

ALLOWED_HOSTS = env.list("PIDASH_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("PIDASH_CSRF_TRUSTED_ORIGINS", default=[])

# Where the database, logs and cache live.
DATA_DIR = Path(env("PIDASH_DATA_DIR", default=str(BASE_DIR / "var")))
if DATA_DIR.exists() and not os.access(DATA_DIR, os.W_OK):
    raise ImproperlyConfigured(
        f"{DATA_DIR} belongs to the account the service runs as, not to you. "
        'Run commands as that account (make shell, make manage cmd="...").'
    )
for _sub in ("", "log"):
    (DATA_DIR / _sub).mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------------------
# Modules. Each one registers its own menu entries, pages and actions; switch one off by
# leaving it out of PIDASH_MODULES.
# --------------------------------------------------------------------------------------
PIDASH_CORE_MODULES = ["pidash.core", "pidash.services"]
PIDASH_MODULES = [
    module
    for module in env.list(
        "PIDASH_MODULES",
        default=[
            "pidash.logs",
            "pidash.prompts",
            "pidash.channels",
            "pidash.recipients",
            "pidash.system",
            "pidash.alerts",
            "pidash.docs",
        ],
    )
    if module
]

INSTALLED_APPS = [
    *PIDASH_CORE_MODULES,
    *PIDASH_MODULES,
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.forms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "pidash.core.middleware.SecurityHeadersMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Every page needs a signed-in user unless a view is explicitly marked public.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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
                "pidash.core.context_processors.pidash",
            ],
        },
    },
]
FORM_RENDERER = "django.forms.renderers.DjangoTemplates"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
        "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 20},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:overview"
LOGOUT_REDIRECT_URL = "core:login"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # a month; it's a private dashboard
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "pidash-sessionid"
CSRF_COOKIE_NAME = "pidash-csrftoken"

LANGUAGE_CODE = "en"
TIME_ZONE = env("PIDASH_TIME_ZONE", default="Europe/Skopje")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = DATA_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
PUBLIC_MODE = env.bool("PIDASH_PUBLIC_MODE", default=False)
if PUBLIC_MODE:  # behind Tailscale serve or another HTTPS proxy on this machine
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

PIDASH_CONTENT_SECURITY_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:"],
    "font-src": ["'self'"],
    "connect-src": ["'self'"],
    "frame-ancestors": ["'none'"],
    "form-action": ["'self'"],
    "base-uri": ["'self'"],
    "object-src": ["'none'"],
}

# --------------------------------------------------------------------------------------
# What the dashboard manages, and how it is allowed to do it.
# --------------------------------------------------------------------------------------
#: The services themselves live in config/services.py — one entry each.
PIDASH_SERVICES_MODULE = env("PIDASH_SERVICES_MODULE", default="config.services")
#: Shared folder for things the dashboard writes for the bots (recipients, later more).
PIDASH_SHARED_CONFIG_DIR = Path(env("PIDASH_SHARED_CONFIG_DIR", default="/etc/bots"))
#: Push notifications for failures (same ntfy topic style as the updater).
PIDASH_NTFY_URL = env("PIDASH_NTFY_URL", default="")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": DATA_DIR / "log" / "pidash.log",
            "maxBytes": 2 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "plain",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
