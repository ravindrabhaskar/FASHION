"""Notification models: inbox rows + device push tokens."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=32)  # social | xp | reward | quote | order | system
    title = models.CharField(max_length=140)
    body = models.CharField(max_length=300, blank=True, default="")
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]


class DeviceToken(TimeStampedUUIDModel):
    """FCM/APNs push registration. Delivery adapter chosen via PUSH_PROVIDER."""

    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    platform = models.CharField(max_length=10, choices=Platform.choices)
    token = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.platform} token for {self.user_id}"
