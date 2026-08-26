from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class AnalyticsEvent(TimeStampedUUIDModel):
    """Append-only analytics event store (see docs/ANALYTICS_EVENT_TAXONOMY.md)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    name = models.CharField(max_length=64, db_index=True)
    properties = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=20, default="mobile")  # mobile | web | server
    request_id = models.CharField(max_length=64, blank=True)
    session_key = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name", "-created_at"]), models.Index(fields=["user", "-created_at"])]
