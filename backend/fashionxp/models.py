"""FashionXP domain models: XP ledger, badges, challenges, rewards (PRD §16–20)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class FashionXPTransaction(TimeStampedUUIDModel):
    """Immutable ledger row — every XP change is exactly one row (PRD §18).

    Never update or delete; corrections are new compensating rows.
    """

    class Reason(models.TextChoices):
        POST_CREATED = "post_created", "Published a post"
        ITEM_ADDED = "item_added", "Wardrobe item added"
        OUTFIT_SAVED = "outfit_saved", "Saved a look"
        DESIGNER_TURN = "designer_turn", "AI designer session"
        LIKE_RECEIVED = "like_received", "Post liked"
        COMMENT_WRITTEN = "comment_written", "Commented"
        FOLLOW_RECEIVED = "follow_received", "Gained a follower"
        CHALLENGE_COMPLETED = "challenge_completed", "Challenge completed"
        BADGE_UNLOCKED = "badge_unlocked", "Badge unlocked"
        REWARD_REDEMPTION = "reward_redemption", "Reward redeemed"
        ADMIN_ADJUSTMENT = "admin_adjustment", "Admin adjustment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xp_transactions"
    )
    amount = models.IntegerField()  # negative only for redemptions/admin clawbacks
    reason = models.CharField(max_length=32, choices=Reason.choices)
    ref_type = models.CharField(max_length=40, blank=True, default="")
    ref_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    balance_after = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "reason", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} {self.amount:+d} ({self.reason})"


class Badge(TimeStampedUUIDModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True, default="")
    icon = models.CharField(max_length=8, default="✦")
    # {"metric": "posts_published", "threshold": 5}
    criteria = models.JSONField(default=dict)
    xp_bonus = models.PositiveIntegerField(default=25)
    is_active = models.BooleanField(default=True)


class UserBadge(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges"
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="holders")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="uniq_user_badge")
        ]


class Challenge(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        LIVE = "LIVE", "Live"
        CLOSED = "CLOSED", "Closed"

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    occasion_slug = models.CharField(max_length=40, blank=True, default="")
    hashtag = models.CharField(max_length=60, blank=True, default="")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    xp_reward = models.PositiveIntegerField(default=100)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.LIVE)

    class Meta:
        ordering = ["-starts_at"]


class ChallengeEntry(TimeStampedUUIDModel):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="entries")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_entries"
    )
    post = models.ForeignKey("social.Post", null=True, on_delete=models.SET_NULL, related_name="+")
    score = models.FloatField(default=0)  # quality-weighted: engagement normalized
    qualified = models.BooleanField(default=False)
    ranked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["challenge", "user"], name="uniq_challenge_entry")
        ]
        ordering = ["-score"]


class Reward(TimeStampedUUIDModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    cost_xp = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    partner = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)


class Redemption(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending fulfilment"
        GRANTED = "GRANTED", "Granted"
        REJECTED = "REJECTED", "Rejected"

    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name="redemptions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reward_redemptions"
    )
    cost_xp = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
