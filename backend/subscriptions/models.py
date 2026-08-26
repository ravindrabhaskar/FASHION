from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class SubscriptionPlan(TimeStampedUUIDModel):
    """PRD §7 plans: style | discover | ai-personal-designer."""

    class Tier(models.TextChoices):
        STYLE = "STYLE", "Style"
        DISCOVER = "DISCOVER", "Discover"
        AI_DESIGNER = "AI_DESIGNER", "AI Personal Designer"

    code = models.SlugField(unique=True)  # e.g. "style-monthly"
    name = models.CharField(max_length=80)
    tier = models.CharField(max_length=20, choices=Tier.choices)
    price_inr = models.PositiveIntegerField()
    billing_interval_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    # Entitlements (admin-editable, consumed via subscriptions.services.get_entitlements)
    ai_text_daily_limit = models.PositiveIntegerField(default=5)
    ai_image_monthly_limit = models.PositiveIntegerField(default=3)
    max_saved_looks = models.PositiveIntegerField(default=20)
    wardrobe_item_limit = models.PositiveIntegerField(default=0)
    designer_chat_enabled = models.BooleanField(default=False)
    customization_requests_enabled = models.BooleanField(default=False)
    features = models.JSONField(default=list, blank=True)  # marketing feature bullets

    class Meta:
        ordering = ["tier", "price_inr"]

    def __str__(self) -> str:
        return f"{self.name} (₹{self.price_inr})"


class UserSubscription(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        TRIALING = "TRIALING", "Trialing"
        ACTIVE = "ACTIVE", "Active"
        PAST_DUE = "PAST_DUE", "Past due"
        CANCELED = "CANCELED", "Canceled"
        EXPIRED = "EXPIRED", "Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.TRIALING)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    provider = models.CharField(max_length=30, blank=True, default="")   # e.g. razorpay
    provider_subscription_id = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    @property
    def is_current(self) -> bool:
        from django.utils import timezone

        return self.status in {self.Status.ACTIVE, self.Status.TRIALING} and \
            self.current_period_end > timezone.now()
