from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class UserProfile(TimeStampedUUIDModel):
    """Extended profile attributes beyond auth basics (1:1 with User)."""

    class Gender(models.TextChoices):
        WOMAN = "WOMAN", "Woman"
        MAN = "MAN", "Man"
        NON_BINARY = "NON_BINARY", "Non-binary"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    display_name = models.CharField(max_length=60, blank=True, default="")
    bio = models.TextField(blank=True, default="", max_length=500)
    city = models.CharField(max_length=80, blank=True, default="")
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=8, default="en")  # AI reply language (PRD §45)

    def __str__(self) -> str:
        return f"Profile<{self.user.email}>"


class StyleProfile(TimeStampedUUIDModel):
    """The structured taste model that powers AI personalization (PRD §8)."""

    class FitPreference(models.TextChoices):
        SLIM = "SLIM", "Slim"
        REGULAR = "REGULAR", "Regular"
        RELAXED = "RELAXED", "Relaxed"
        MIXED = "MIXED", "Depends on outfit"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="style_profile"
    )
    preferred_styles = models.JSONField(default=list, blank=True)   # ["minimal", "streetwear", ...]
    favorite_colors = models.JSONField(default=list, blank=True)
    avoided_colors = models.JSONField(default=list, blank=True)
    fit_preference = models.CharField(max_length=12, choices=FitPreference.choices, blank=True, default="")
    budget_min = models.PositiveIntegerField(null=True, blank=True)
    budget_max = models.PositiveIntegerField(null=True, blank=True)
    clothing_preferences = models.JSONField(default=dict, blank=True)  # {"kurtas": True, "jeans": True}
    common_occasions = models.JSONField(default=list, blank=True)      # occasion slugs
    traditional_modern_balance = models.PositiveSmallIntegerField(
        default=50, help_text="0 = fully modern, 100 = fully traditional"
    )

    completion_cache = models.PositiveSmallIntegerField(default=0)

    def __str__(self) -> str:
        return f"StyleProfile<{self.user.email}>"

    def compute_completion(self) -> int:
        """0-100 score used for activation analytics and progressive profiling."""
        checks = [
            bool(self.preferred_styles),
            bool(self.favorite_colors),
            bool(self.fit_preference),
            self.budget_max is not None,
            bool(self.common_occasions),
            bool(self.clothing_preferences),
        ]
        return round(100 * sum(bool(c) for c in checks) / len(checks))
