"""
Local settings

- Run in Debug mode

- Use console backend for emails

- Add Django Debug Toolbar
- Add django-extensions as app
"""

from .base import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", default=True)
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="m,*Ob~?A=tK0-RB;J,qV*[<SWZ]b@,9-BUk+Uy0#ltBwoziA`H"
)

# Mail settings
# ------------------------------------------------------------------------------

EMAIL_PORT = 1025

EMAIL_HOST = "localhost"
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)


# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
INSTALLED_APPS += [
    "debug_toolbar",
]

INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "192.168.99.100"]
ALLOWED_HOSTS = INTERNAL_IPS + ["localhost", "[::1]"]


import os
import socket

# tricks to have debug toolbar when developing with docker
if os.environ.get("USE_DOCKER") == "yes":
    ip = socket.gethostbyname(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1"]

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += [
    "django_extensions",
]

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Your local stuff: Below this line define 3rd party library settings
# ------------------------------------------------------------------------------

# If DEBUG_USERNAME is set the bot will always join the twitch channel
# for the specified user regardless of whether or not it is live
# (useful for testing purposes). Note that the specified user must exist and
# have a linked twitch channel.
DEBUG_USERNAME = env("DEBUG_USERNAME", default="")
