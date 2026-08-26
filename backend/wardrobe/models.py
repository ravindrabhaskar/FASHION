"""Digital wardrobe: user-owned garments with AI-extracted attributes (PRD §11)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class WardrobeItem(TimeStampedUUIDModel):
    """One physical garment the user owns. Attributes are AI-extracted from a photo."""

    class Category(models.TextChoices):
        TOPS = "tops", "Tops"
        BOTTOMS = "bottoms", "Bottoms"
        DRESSES = "dresses", "Dresses"
        OUTERWEAR = "outerwear", "Outerwear"
        FOOTWEAR = "footwear", "Footwear"
        ACCESSORIES = "accessories", "Accessories"
        ETHNIC = "ethnic", "Ethnic & Traditional"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting analysis"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Analysis failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wardrobe_items"
    )
    name = models.CharField(max_length=120, blank=True, default="Untitled piece")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    MEDIA_DOMAIN = "wardrobe"
    image = models.ImageField(upload_to="wardrobe/", blank=True, default="", max_length=500)

    # AI-extracted attributes (editable by the user)
    color_primary = models.CharField(max_length=40, blank=True, default="")
    color_hex = models.CharField(max_length=9, blank=True, default="")
    fabric = models.CharField(max_length=60, blank=True, default="")
    pattern = models.CharField(max_length=60, blank=True, default="")
    formality = models.PositiveSmallIntegerField(default=3)
    seasons = models.JSONField(default=list, blank=True)          # e.g. ["summer", "monsoon"]
    occasion_slugs = models.JSONField(default=list, blank=True)   # registry occasion slugs
    style_tags = models.JSONField(default=list, blank=True)
    attributes = models.JSONField(default=dict, blank=True)       # full analysis snapshot

    notes = models.CharField(max_length=300, blank=True, default="")
    favorite = models.BooleanField(default=False)
    times_worn = models.PositiveIntegerField(default=0)
    last_worn_at = models.DateTimeField(null=True, blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.category}) for {self.user_id}"
