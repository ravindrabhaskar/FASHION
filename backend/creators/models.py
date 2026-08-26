"""Creator system: profile, eligibility, portfolio, analytics (PRD §21)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class CreatorProfile(TimeStampedUUIDModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="creator_profile"
    )
    handle = models.SlugField(unique=True)
    niche = models.CharField(max_length=80, blank=True, default="")  # e.g. "saree styling"
    platforms = models.JSONField(default=dict, blank=True)          # {"instagram": "url"}
    audience_size = models.PositiveIntegerField(default=0)
    is_eligible = models.BooleanField(default=False)
    eligibility_checked_at = models.DateTimeField(null=True, blank=True)
    stats = models.JSONField(default=dict, blank=True)              # cached reach/engagement
    stats_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"@{self.handle}"


class PortfolioItem(TimeStampedUUIDModel):
    creator = models.ForeignKey(
        CreatorProfile, on_delete=models.CASCADE, related_name="portfolio_items"
    )
    title = models.CharField(max_length=140)
    post = models.ForeignKey(
        "social.Post", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    media_url = models.URLField(blank=True, default="")
    metrics = models.JSONField(default=dict, blank=True)  # {views, saves, conversions}

    class Meta:
        ordering = ["-created_at"]
