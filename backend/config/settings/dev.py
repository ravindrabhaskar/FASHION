"""Development settings — permissive defaults for local work."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Allow Expo web / device testing origins in dev.
CORS_ALLOW_ALL_ORIGINS = True

# Dev convenience: browsable API after our envelope renderer.
REST_FRAMEWORK = {**REST_FRAMEWORK}  # noqa: F405
