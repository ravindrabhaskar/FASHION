"""Order models with an explicit state machine + transition audit trail (PRD §30)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Order(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        AWAITING_PAYMENT = "AWAITING_PAYMENT", "Awaiting payment"
        PAID = "PAID", "Paid"
        IN_PRODUCTION = "IN_PRODUCTION", "In production"      # customized/made-to-order
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    seller_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sales",
    )
    designer = models.ForeignKey(
        "designers.DesignerProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    brand = models.ForeignKey(
        "brands.BrandProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    quote_request = models.ForeignKey(
        "marketplace.QuoteRequest", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="order",
    )
    product = models.ForeignKey(
        "marketplace.Product", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    title_snapshot = models.CharField(max_length=160)
    variant_snapshot = models.JSONField(default=dict, blank=True)  # {Size: M, Colour: Ivory}
    quantity = models.PositiveSmallIntegerField(default=1)
    amount_inr = models.PositiveIntegerField()
    commission_inr = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    shipping_address = models.JSONField(default=dict, blank=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["seller_user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]


class OrderEvent(TimeStampedUUIDModel):
    """Append-only transition log for support/audit."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    note = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ["created_at"]
