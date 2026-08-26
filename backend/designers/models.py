"""Local designer profiles, verification and storefronts (PRD §22–23)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class DesignerProfile(TimeStampedUUIDModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="designer_profile"
    )
    slug = models.SlugField(unique=True)
    studio_name = models.CharField(max_length=120)
    tagline = models.CharField(max_length=160, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    city = models.CharField(max_length=80, blank=True, default="")
    specialities = models.JSONField(default=list, blank=True)   # ["bridal-wear", "handloom", ...]
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True)
    instagram = models.CharField(max_length=120, blank=True, default="")
    is_accepting_custom_requests = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["city", "-verified"])]

    def __str__(self) -> str:
        return f"{self.studio_name} ({self.slug})"


class PortfolioImage(TimeStampedUUIDModel):
    designer = models.ForeignKey(
        DesignerProfile, on_delete=models.CASCADE, related_name="portfolio_images"
    )
    MEDIA_DOMAIN = "designer_portfolio"
    image = models.ImageField(upload_to="designer_portfolio/", max_length=500)
    caption = models.CharField(max_length=160, blank=True, default="")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]
