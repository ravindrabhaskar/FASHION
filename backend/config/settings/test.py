"""Test settings — fast, hermetic, deterministic."""
from .base import *  # noqa: F401,F403

DEBUG = False

# Deterministic, in-process everything.
CACHES = {  # noqa: F811 - intentional override
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "fashionxp-test",
    }
}
CELERY_TASK_ALWAYS_EAGER = True  # noqa: F811 - intentional override
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

AI_PROVIDER = "mock"
SMS_PROVIDER = "console"
