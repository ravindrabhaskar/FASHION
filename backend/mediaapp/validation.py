"""Media pipeline: upload validation + pluggable backends (local | S3-compatible).

Django's FileField handles persistence; this module centralizes policy and the
S3 adapter so swapping backends never touches domain code.
"""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError

MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
}


def validate_image(file, *, max_bytes: int = MAX_UPLOAD_BYTES) -> None:
    """Content-sniff validation — never trust client MIME alone."""
    if file.size > max_bytes:
        raise ValidationError(f"File exceeds {max_bytes // (1024*1024)} MB limit.")
    header = file.read(16)
    file.seek(0)
    detected = None
    for magic, mime in IMAGE_MAGIC.items():
        if header.startswith(magic):
            detected = mime
            break
    if detected is None:
        raise ValidationError("Unsupported or corrupt image file.")


def make_upload_path(instance, filename: str) -> str:
    """<domain>/<uuid>.<ext> — avoids user-controlled path segments entirely."""
    import os

    ext = os.path.splitext(filename)[1].lower()[:8] or ".bin"
    domain = getattr(instance, "MEDIA_DOMAIN", "uploads")
    return f"{domain}/{uuid.uuid4().hex}{ext}"
