"""Brand accounts & storefronts (PRD §23)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class BrandProfile(TimeStampedUUIDModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="brand_profile"
    )
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    about = models.TextField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    logo = models.ImageField(upload_to="brand_logos/", blank=True, default="", max_length=500)
    city = models.CharField(max_length=80, blank=True, default="")
    categories = models.JSONField(default=list, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
