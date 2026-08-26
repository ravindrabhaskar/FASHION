"""Social fashion network models (PRD §13–16)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Follow(TimeStampedUUIDModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed_to"], name="uniq_follow")
        ]

    def __str__(self) -> str:
        return f"{self.follower_id} → {self.followed_to_id}"


class Post(TimeStampedUUIDModel):
    """A shared look: own photo or an outfit/wardrobe piece with editable AI metadata."""

    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"
        REMOVED = "REMOVED", "Removed by moderation"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    caption = models.TextField(max_length=1000, blank=True, default="")
    occasion = models.CharField(max_length=40, blank=True, default="")
    MEDIA_DOMAIN = "posts"
    image = models.ImageField(upload_to="posts/", blank=True, default="", max_length=500)
    source_outfit = models.ForeignKey(
        "fashion.GeneratedOutfit", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="posts",
    )  # look reference renders its concept image when no photo uploaded
    ai_metadata = models.JSONField(default=dict, blank=True)  # suggested caption/tags, editable
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PUBLISHED)

    # Denormalized engagement counters for deterministic feed ranking.
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    city_snapshot = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]


class PostItemTag(TimeStampedUUIDModel):
    """Shop-this-look component: a tagged piece that can resolve to a product."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="item_tags")
    wardrobe_item = models.ForeignKey(
        "wardrobe.WardrobeItem", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="post_tags",
    )
    label = models.CharField(max_length=120)  # e.g. "Emerald silk kurta set"
    position = models.PositiveSmallIntegerField(default=0)
    product = models.ForeignKey(
        "marketplace.Product", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="post_tags",
    )  # linked in Phase 4 shop-this-look flow

    class Meta:
        ordering = ["position"]


class Like(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="uniq_like")]


class Comment(TimeStampedUUIDModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    text = models.TextField(max_length=500)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["post", "created_at"])]


class SavedPost(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="uniq_saved_post")]
        ordering = ["-created_at"]


class Report(TimeStampedUUIDModel):
    class TargetType(models.TextChoices):
        POST = "post", "Post"
        COMMENT = "comment", "Comment"
        USER = "user", "User"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        ABUSE = "abuse", "Abuse or harassment"
        NSFW = "nsfw", "Nudity or sexual content"
        IP = "ip", "Intellectual property"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DISMISSED = "DISMISSED", "Dismissed"
        ACTIONED = "ACTIONED", "Action taken"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_filed"
    )
    target_type = models.CharField(max_length=10, choices=TargetType.choices)
    target_id = models.CharField(max_length=64, db_index=True)
    reason = models.CharField(max_length=10, choices=Reason.choices)
    details = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reports_resolved",
    )
