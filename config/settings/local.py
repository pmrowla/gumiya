"""
Local settings

- Run in Debug mode

- Use console backend for emails

- Add Django Debug Toolbar
- Add django-extensions as app
"""

import socket

from .base import *  # noqa
from .base import env

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = True
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "192.168.99.100"]

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

# whitenoise
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405

# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# tricks to have debug toolbar when developing with docker
if env("USE_DOCKER") == "yes":
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

ALLOWED_HOSTS = INTERNAL_IPS + ["localhost", "[::1]"]

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]  # noqa F405

# Your local stuff: Below this line define 3rd party library settings
# ------------------------------------------------------------------------------

# If DEBUG_USERNAME is set the bot will always join the twitch channel
# for the specified user regardless of whether or not it is live
# (useful for testing purposes). Note that the specified user must exist and
# have a linked twitch channel.
DEBUG_USERNAME = env("DEBUG_USERNAME", default="")
