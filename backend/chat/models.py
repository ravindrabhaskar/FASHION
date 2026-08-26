"""Buyer↔seller chat with moderation hooks (PRD §28)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Thread(TimeStampedUUIDModel):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_threads"
    )
    seller_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_threads"
    )
    designer = models.ForeignKey(
        "designers.DesignerProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="threads",
    )
    product = models.ForeignKey(
        "marketplace.Product", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="threads",
    )
    order = models.ForeignKey(
        "orders.Order", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="threads",
    )
    quote_request = models.ForeignKey(
        "marketplace.QuoteRequest", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="threads",
    )
    subject = models.CharField(max_length=140, blank=True, default="")
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["buyer", "-updated_at"])]


class Message(TimeStampedUUIDModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    body = models.TextField(max_length=2000)
    read_at = models.DateTimeField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["created_at"]
