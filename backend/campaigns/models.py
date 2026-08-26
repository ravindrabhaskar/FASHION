"""Brand↔creator campaigns (PRD §29)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Campaign(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Accepting applications"
        CLOSED = "CLOSED", "Closed for applications"
        COMPLETED = "COMPLETED", "Completed"

    brand_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="campaigns"
    )
    brand = models.ForeignKey(
        "brands.BrandProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="campaigns",
    )
    title = models.CharField(max_length=140)
    brief = models.TextField(max_length=3000)
    deliverables = models.JSONField(default=list, blank=True)   # ["2 reels", "1 story set"]
    budget_inr = models.PositiveIntegerField()
    payout_inr = models.PositiveIntegerField(null=True, blank=True)
    min_audience = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["-created_at"]


class Application(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="applications")
    creator = models.ForeignKey(
        "creators.CreatorProfile", on_delete=models.CASCADE, related_name="applications",
    )
    pitch = models.TextField(max_length=1500, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    performance = models.JSONField(default=dict, blank=True)  # filled post-campaign

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["campaign", "creator"], name="uniq_campaign_application")
        ]
