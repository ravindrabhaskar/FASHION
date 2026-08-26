"""Payment models: provider-agnostic attempts + idempotent webhook log (PRD §31)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Payment(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        AUTHORIZED = "AUTHORIZED", "Authorized"
        CAPTURED = "CAPTURED", "Captured"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments",
    )
    provider = models.CharField(max_length=30)                 # mock | razorpay
    provider_order_id = models.CharField(max_length=100, blank=True, default="")
    provider_payment_id = models.CharField(max_length=100, blank=True, default="")
    amount_inr = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CREATED)
    idempotency_key = models.CharField(max_length=64, unique=True)
    error = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]


class WebhookEvent(TimeStampedUUIDModel):
    """Raw webhook storage — unique event_id makes processing idempotent."""

    provider = models.CharField(max_length=30)
    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=80, blank=True, default="")
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True, default="")


class PaymentMethodRecord(TimeStampedUUIDModel):
    """Tokenized method references only — raw card data never touches FashionXP."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods",
    )
    provider = models.CharField(max_length=30)
    provider_token = models.CharField(max_length=200)
    label = models.CharField(max_length=60, blank=True, default="")
    is_default = models.BooleanField(default=False)
