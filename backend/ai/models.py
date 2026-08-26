"""AI domain models: usage ledger for cost observability (PRD §31–32)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class AIUsageLog(TimeStampedUUIDModel):
    """One row per AI operation — provider-agnostic cost/latency observability."""

    class Feature(models.TextChoices):
        STYLIST_ANALYSIS = "stylist_analysis", "Stylist photo analysis"
        STYLIST_RECOMMEND = "stylist_recommend", "Outfit recommendation"
        DESIGNER_CHAT = "designer_chat", "Conversational designer"
        OUTFIT_IMAGE = "outfit_image", "Outfit image generation"
        WARDROBE_EXTRACT = "wardrobe_extract", "Wardrobe attribute extraction"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CACHED = "CACHED", "Served from cache"
        REJECTED_SAFETY = "REJECTED_SAFETY", "Rejected by safety filter"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="ai_usage",
    )
    feature = models.CharField(max_length=32, choices=Feature.choices)
    provider = models.CharField(max_length=40)
    model = models.CharField(max_length=80, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUCCESS)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    cache_hit = models.BooleanField(default=False)
    request_hash = models.CharField(max_length=64, blank=True, db_index=True)
    error = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["feature", "-created_at"]),
            models.Index(fields=["user", "feature", "-created_at"]),
        ]
