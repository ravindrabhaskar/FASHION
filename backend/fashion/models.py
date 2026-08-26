"""Fashion domain models: occasions, saved looks, conversational designer state."""

from django.conf import settings
from django.db import models

from ai.schemas import DesignState
from core.models import TimeStampedUUIDModel


class Occasion(TimeStampedUUIDModel):
    """Seeded from fashion.registry.OCCASIONS; editable metadata lives here."""

    slug = models.SlugField(unique=True)
    label = models.CharField(max_length=60)
    description = models.TextField(blank=True, default="")
    formality = models.PositiveSmallIntegerField(default=3)
    palette_bias = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["formality", "label"]

    def __str__(self) -> str:
        return self.label


class AIConversation(TimeStampedUUIDModel):
    """Conversational AI Designer thread with evolving design state."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="designer_conversations"
    )
    title = models.CharField(max_length=120, blank=True, default="New design")
    design_state = models.JSONField(default=dict, blank=True)  # DesignState snapshot
    occasion = models.CharField(max_length=40, blank=True, default="")
    budget_inr = models.PositiveIntegerField(null=True, blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]

    def get_design_state(self) -> DesignState | None:
        if not self.design_state:
            return None
        try:
            return DesignState.model_validate(self.design_state)
        except Exception:
            return None


class AIMessage(TimeStampedUUIDModel):
    class Role(models.TextChoices):
        USER = "USER", "User"
        ASSISTANT = "ASSISTANT", "Assistant"
        SYSTEM = "SYSTEM", "System"

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    content = models.TextField()
    changes = models.JSONField(default=list, blank=True)     # change log for assistant turns
    design_version = models.PositiveIntegerField(null=True, blank=True)
    image_job_id = models.UUIDField(null=True, blank=True)   # links to GeneratedOutfit job

    class Meta:
        ordering = ["created_at"]


class GeneratedOutfit(TimeStampedUUIDModel):
    """A look: stylist result or designer concept. Saveable, shareable, customizable."""

    class Source(models.TextChoices):
        STYLIST = "STYLIST", "AI Stylist"
        DESIGNER = "DESIGNER", "AI Designer"
        CUSTOMIZE = "CUSTOMIZE", "Customize This Look"
        WARDROBE = "WARDROBE", "From My Closet"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        GENERATING = "GENERATING", "Generating"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="outfits"
    )
    source = models.CharField(max_length=12, choices=Source.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.COMPLETED)

    title = models.CharField(max_length=140, blank=True, default="")
    occasion = models.CharField(max_length=40, blank=True, default="")
    budget_inr = models.PositiveIntegerField(null=True, blank=True)

    recommendation = models.JSONField(default=dict, blank=True)   # RecommendationResult payload
    design_state = models.JSONField(default=dict, blank=True)     # DesignState for designer/custom looks
    image_prompt = models.TextField(blank=True, default="")
    MEDIA_DOMAIN = "outfits"
    image = models.ImageField(upload_to="outfits/", blank=True, default="", max_length=500)

    conversation = models.ForeignKey(
        AIConversation, null=True, blank=True, on_delete=models.SET_NULL, related_name="outfits"
    )
    source_outfit = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="customized_versions",
    )  # traceability: customized look → original look
    version = models.PositiveIntegerField(default=1)

    saved = models.BooleanField(default=False)
    saved_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "saved", "-saved_at"]),
            models.Index(fields=["source", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_source_display()} look for {self.user_id} ({self.status})"
