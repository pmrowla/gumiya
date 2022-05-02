"""
Production Configurations

- Use Amazon's S3 for storing static files and uploaded media
- Use mailgun to send emails
- Use Redis for cache

- Use sentry for error logging


"""
import logging

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *  # noqa
from .base import env

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")


# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.security
# and https://docs.djangoproject.com/en/dev/howto/deployment/checklist/#run-manage-py-check-deploy

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
)
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True
)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["gumiya.pmrowla.com"],
)
# END SITE CONFIGURATION


# STORAGE CONFIGURATION
# ------------------------------------------------------------------------------
# Uploaded Media Files
# ------------------------
# See: http://django-storages.readthedocs.io/en/latest/index.html
INSTALLED_APPS += ["storages"]  # noqa F405

AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
AWS_AUTO_CREATE_BUCKET = True
AWS_QUERYSTRING_AUTH = False

# AWS cache settings, don't change unless you know what you're doing:
_AWS_EXPIRY = 60 * 60 * 24 * 7

AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate"
}
AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME", default=None)
AWS_S3_CUSTOM_DOMAIN = env("DJANGO_AWS_S3_CUSTOM_DOMAIN", default=None)
aws_s3_domain = AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# URL that handles the media served from MEDIA_ROOT, used for managing
# stored files.
MEDIA_URL = f"https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/"
DEFAULT_FILE_STORAGE = "twitch_osu_bot.utils.storages.MediaRootS3Boto3Storage"


# Static Assets
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# COMPRESSOR
# ------------------------------------------------------------------------------

COMPRESS_OFFLINE = True
COMPRESS_URL = STATIC_URL  # noqa F405
COMPRESS_ENABLED = env.bool("COMPRESS_ENABLED", default=True)
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}

# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL", default="Gumiya staff <noreply@gumiya.pmrowla.com>"
)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[gumiya]")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# Anymail with Mailgun
INSTALLED_APPS += ["anymail"]  # noqa F405
ANYMAIL = {
    "MAILGUN_API_KEY": env("DJANGO_MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
    "MAILGUN_API_URL": env("MAILGUN_API_URL", default="https://api.mailgun.net/v3"),
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
DATABASES["default"] = env.db("DATABASE_URL")  # noqa F405
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405

# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        },
    }
}

# Sentry Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
            "%(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        # Errors logged by the SDK itself
        "sentry_sdk": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

SENTRY_DSN = env("DJANGO_SENTRY_DSN")
SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)

sentry_logging = LoggingIntegration(
    level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
integrations = [sentry_logging, DjangoIntegration(), RedisIntegration()]
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=integrations,
    environment=env("SENTRY_ENVIRONMENT", default="production"),
    traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
)

# Custom Admin URL, use {% url 'admin:index' %}
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Your production stuff: Below this line define 3rd party library settings
# ------------------------------------------------------------------------------
