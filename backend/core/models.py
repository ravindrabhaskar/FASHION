import uuid

from django.conf import settings
from django.db import models


class TimeStampedUUIDModel(models.Model):
    """Abstract base: UUID primary key + created/updated timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SystemConfig(TimeStampedUUIDModel):
    """Admin-editable operational configuration (quotas, rates, thresholds).

    Anything likely to change operationally lives here instead of code.
    Changes are protected by permissions and recorded in AuditLog.
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key


class FeatureFlag(TimeStampedUUIDModel):
    """Independent enable/disable switches for major systems."""

    key = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return f"{self.key}={'on' if self.enabled else 'off'}"


class AuditLog(TimeStampedUUIDModel):
    """Immutable audit trail for sensitive operations."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries"
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=64, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} → {self.target_type}:{self.target_id}"


def record_audit(*, actor=None, action: str, target=None, before=None, after=None,
                 metadata: dict | None = None) -> AuditLog:
    from core.middleware import request_id_var

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target.__class__.__name__ if target is not None else "",
        target_id=str(getattr(target, "pk", "") or ""),
        before=before,
        after=after,
        metadata=metadata or {},
        request_id=request_id_var.get() or "",
    )
