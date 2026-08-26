"""FashionXP engine: awards, levels, badges, challenges, leaderboards, rewards.

Rules live in DB-backed config (`core.services.get_config`) so operations can tune
XP values without deploys. The ledger is append-only; balances are derived.
"""
import logging
from dataclasses import dataclass

from django.db.models import Sum
from django.utils import timezone

from analytics.services import record_event
from core.exceptions import AppError
from core.services import get_config
from fashionxp.models import (
    Badge,
    Challenge,
    ChallengeEntry,
    FashionXPTransaction,
    Redemption,
    Reward,
    UserBadge,
)

logger = logging.getLogger(__name__)

LEVELS = [
    (0, "Rookie"),
    (200, "Style Enthusiast"),
    (500, "Trendsetter"),
    (1000, "Fashion Icon"),
    (2500, "Style Legend"),
]

# metric -> (label, callable(user) -> int)
_BADGE_METRICS = {
    "posts_published": lambda u: _count(u, "posts", status="PUBLISHED"),
    "wardrobe_items": lambda u: _count(u, "wardrobe_items", archived=False),
    "saved_looks": lambda u: _count(u, "outfits", saved=True),
    "followers": lambda u: _followers(u),
}


def _count(user, rel, **filters) -> int:
    try:
        return getattr(user, rel).filter(**filters).count()
    except Exception:  # noqa: BLE001 - relation may not exist for anonymous rows
        return 0


def _followers(user) -> int:
    from social.models import Follow

    return Follow.objects.filter(followed_to=user).count()


@dataclass(frozen=True)
class LevelInfo:
    name: str
    level: int
    current_xp: int
    next_threshold: int | None
    progress_percent: int


def xp_value(reason: str) -> int:
    return int(get_config(f"xp.{reason}", 0) or 0)


def daily_cap() -> int:
    return int(get_config("xp.daily_earn_cap", 100) or 0)


def balance(user) -> int:
    total = FashionXPTransaction.objects.filter(user=user).aggregate(s=Sum("amount"))["s"]
    return int(total or 0)


def earned_today(user) -> int:
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = FashionXPTransaction.objects.filter(
        user=user, amount__gt=0, created_at__gte=start
    ).aggregate(s=Sum("amount"))["s"]
    return int(total or 0)


def level_for(xp_total: int) -> LevelInfo:
    current_name, current_floor = LEVELS[0][1], LEVELS[0][0]
    index = 0
    for i, (floor, name) in enumerate(LEVELS):
        if xp_total >= floor:
            current_name, current_floor, index = name, floor, i
    next_threshold = LEVELS[index + 1][0] if index + 1 < len(LEVELS) else None
    if next_threshold is None:
        progress = 100
    else:
        span = next_threshold - current_floor
        progress = min(100, int((xp_total - current_floor) / max(span, 1) * 100))
    return LevelInfo(
        name=current_name,
        level=index + 1,
        current_xp=xp_total,
        next_threshold=next_threshold,
        progress_percent=progress,
    )


def award(user, reason: str, *, ref_type: str = "", ref_id: str = "",
          amount_override: int | None = None) -> FashionXPTransaction | None:
    """Append one XP row. Respects the daily earn cap. Never raises on cap."""
    amount = amount_override if amount_override is not None else xp_value(reason)
    if amount <= 0:
        return None
    cap = daily_cap()
    if cap and earned_today(user) + amount > cap:
        logger.info("XP daily cap reached for %s (%s)", user_id_of(user), reason)
        return None

    new_balance = balance(user) + amount
    txn = FashionXPTransaction.objects.create(
        user=user, amount=amount, reason=reason,
        ref_type=ref_type, ref_id=str(ref_id)[:64],
        balance_after=max(0, new_balance),
    )
    previous_level = level_for(new_balance - amount)
    after_level = level_for(new_balance)
    ensure_badges(user)
    if after_level.name != previous_level.name:
        record_event(user=user, name="xp_level_up",
                     properties={"level": after_level.name, "xp": new_balance})
        notify_user(
            user, type="xp", title=f"Level up: {after_level.name} ✦",
            body="You unlocked a new style level. Keep going!",
        )
    return txn


def user_id_of(user):
    return getattr(user, "id", user)


def spend(user, *, amount: int, reason: str, ref_type: str = "", ref_id: str = "") -> FashionXPTransaction:
    """Deduct XP atomically; raises insufficient_xp when the balance is too low."""
    if amount <= 0:
        raise AppError("Invalid XP amount.", code="invalid_amount")
    current = balance(user)
    if current < amount:
        raise AppError(
            f"You need {amount - current} more XP for that.", code="insufficient_xp"
        )
    return FashionXPTransaction.objects.create(
        user=user, amount=-amount, reason=reason,
        ref_type=ref_type, ref_id=str(ref_id)[:64],
        balance_after=current - amount,
    )


def ensure_badges(user) -> list[str]:
    """Evaluate badge criteria; award any newly-earned badges (+bonus XP rows)."""
    earned: list[str] = []
    metrics = {
        "posts_published": _BADGE_METRICS["posts_published"](user),
        "wardrobe_items": _BADGE_METRICS["wardrobe_items"](user),
        "saved_looks": _BADGE_METRICS["saved_looks"](user),
        "followers": _BADGE_METRICS["followers"](user),
    }
    owned = set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))
    for badge in Badge.objects.filter(is_active=True):
        if badge.code in owned:
            continue
        metric = (badge.criteria or {}).get("metric")
        threshold = int((badge.criteria or {}).get("threshold", 0))
        if metric in metrics and metrics[metric] >= threshold > 0:
            UserBadge.objects.create(user=user, badge=badge)
            earned.append(badge.code)
            FashionXPTransaction.objects.create(
                user=user, amount=badge.xp_bonus, reason=FashionXPTransaction.Reason.BADGE_UNLOCKED,
                ref_type="badge", ref_id=badge.code,
                balance_after=balance(user),
            )
            record_event(user=user, name="badge_unlocked",
                         properties={"badge": badge.code})
    return earned


def leaderboard(*, scope: str = "global", city: str = "", challenge_slug: str = "",
                limit: int = 20) -> list[dict]:
    """Deterministic ranking. Challenges are quality-weighted by engagement score."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if scope == "challenge":
        try:
            challenge = Challenge.objects.get(slug=challenge_slug)
        except Challenge.DoesNotExist as exc:
            raise AppError("Unknown challenge.", code="unknown_challenge") from exc
        entries = challenge.entries.select_related("user").order_by("-score", "created_at")[:limit]
        return [
            {
                "user_id": str(e.user_id), "display_name": e.user.profile.display_name or e.user.full_name,
                "score": round(e.score, 2), "qualified": e.qualified, "rank": i + 1,
            }
            for i, e in enumerate(entries)
        ]

    qs = User.objects.filter(is_active=True)
    if scope == "city" and city:
        qs = qs.filter(profile__city__iexact=city)
    top = (
        FashionXPTransaction.objects.filter(user__in=qs)
        .values("user")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:limit]
    )
    users = {u.id: u for u in User.objects.filter(id__in=[t["user"] for t in top])}
    out = []
    for i, row in enumerate(top):
        u = users.get(row["user"])
        if not u:
            continue
        out.append({
            "user_id": str(u.id),
            "display_name": (getattr(u, "profile", None) and u.profile.display_name) or u.full_name,
            "total_xp": int(row["total"]),
            "level": level_for(int(row["total"])).name,
            "rank": i + 1,
        })
    return out


def enroll_challenge(user, challenge: Challenge, post=None) -> ChallengeEntry:
    now = timezone.now()
    if not (challenge.starts_at <= now <= challenge.ends_at):
        raise AppError("This challenge isn't live right now.", code="challenge_not_live")
    entry, created = ChallengeEntry.objects.get_or_create(
        challenge=challenge, user=user, defaults={"post": post}
    )
    if created:
        award(user, "challenge_completed", ref_type="challenge", ref_id=challenge.slug)
        record_event(user=user, name="challenge_enrolled",
                     properties={"challenge": challenge.slug})
    elif post is not None and entry.post is None:
        entry.post = post
        entry.save(update_fields=["post"])
    rescore_entry(entry)
    return entry


def rescore_entry(entry: ChallengeEntry) -> ChallengeEntry:
    """Quality-weighted score: likes*2 + comments*5 on the linked post."""
    post = entry.post
    raw = float(post.like_count) * 2 + float(post.comment_count) * 5 if post is not None else 0.0
    entry.score = raw
    entry.qualified = raw > 0
    entry.ranked_at = timezone.now()
    entry.save(update_fields=["score", "qualified", "ranked_at"])
    return entry


def redeem_reward(user, reward: Reward) -> Redemption:
    pending = Redemption.objects.filter(
        user=user, reward=reward, status=Redemption.Status.PENDING
    ).exists()
    if pending:
        raise AppError("You already have a pending redemption for this reward.",
                       code="redemption_pending")
    if reward.stock is not None and reward.stock <= 0:
        raise AppError("This reward just went out of stock.", code="reward_out_of_stock")

    redemption = Redemption.objects.create(user=user, reward=reward, cost_xp=reward.cost_xp)
    try:
        spend(user, amount=reward.cost_xp, reason=FashionXPTransaction.Reason.REWARD_REDEMPTION,
              ref_type="reward", ref_id=str(redemption.id))
    except AppError:
        redemption.delete()
        raise
    if reward.stock is not None:
        Reward.objects.filter(pk=reward.pk).update(stock=reward.stock - 1)
    redemption.status = Redemption.Status.GRANTED
    redemption.save(update_fields=["status"])
    record_event(user=user, name="reward_redeemed",
                 properties={"reward": reward.code, "cost_xp": reward.cost_xp})
    notify_user(
        user, type="reward", title=f"{reward.name} unlocked 🎁",
        body="Your reward is confirmed — check your email for fulfilment details.",
    )
    return redemption


# Late import to avoid circularity with the notifications app.
def notify_user(user, *, type: str, title: str, body: str, data: dict | None = None) -> None:
    try:
        from notifications.services import notify

        notify(user, type=type, title=title, body=body, data=data or {})
    except Exception:  # noqa: BLE001 - notifications must never break XP flows
        logger.exception("notify failed")
