"""Central entitlement service.

Every plan/quota check in the codebase goes through here — never scatter
`if user.plan == ...` checks across domains (PRD §33).
"""
from dataclasses import dataclass, field

from django.utils import timezone

from subscriptions.models import SubscriptionPlan, UserSubscription

FREE_ENTITLEMENTS = {
    "ai_text_daily_limit": 3,
    "ai_image_monthly_limit": 2,
    "max_saved_looks": 10,
    "wardrobe_item_limit": 15,
    "designer_chat_enabled": False,
    "customization_requests_enabled": False,
    "tier": None,
}


@dataclass(frozen=True)
class Entitlements:
    tier: str | None
    ai_text_daily_limit: int
    ai_image_monthly_limit: int
    max_saved_looks: int
    wardrobe_item_limit: int
    designer_chat_enabled: bool
    customization_requests_enabled: bool
    subscription: UserSubscription | None = field(default=None, repr=False)

    @property
    def is_paid(self) -> bool:
        return self.tier is not None


def get_active_subscription(user) -> UserSubscription | None:
    subs = (
        UserSubscription.objects.filter(
            status__in=[UserSubscription.Status.ACTIVE, UserSubscription.Status.TRIALING],
            current_period_end__gt=timezone.now(),
        )
        .select_related("plan")
        .order_by("-current_period_end")
    )
    # Prefer the highest tier among concurrent subscriptions.
    best = max(subs, key=lambda s: list(SubscriptionPlan.Tier.values).index(s.plan.tier), default=None)
    return best


def get_entitlements(user) -> Entitlements:
    sub = get_active_subscription(user)
    if not sub or not sub.is_current:
        return Entitlements(**FREE_ENTITLEMENTS)
    plan = sub.plan
    return Entitlements(
        tier=plan.tier,
        ai_text_daily_limit=plan.ai_text_daily_limit,
        ai_image_monthly_limit=plan.ai_image_monthly_limit,
        max_saved_looks=plan.max_saved_looks,
        wardrobe_item_limit=plan.wardrobe_item_limit,
        designer_chat_enabled=plan.designer_chat_enabled,
        customization_requests_enabled=plan.customization_requests_enabled,
        subscription=sub,
    )


class QuotaExceeded(Exception):
    def __init__(self, scope: str, limit: int):
        self.scope = scope
        self.limit = limit
        super().__init__(f"Quota exceeded for {scope} (limit {limit})")


def assert_within_quota(entitlements: Entitlements, scope: str, used: int) -> None:
    limits = {
        "ai_text": entitlements.ai_text_daily_limit,
        "ai_image": entitlements.ai_image_monthly_limit,
        "saved_looks": entitlements.max_saved_looks,
        "wardrobe_items": entitlements.wardrobe_item_limit,
    }
    limit = limits.get(scope)
    if limit is None:
        return
    if used >= limit:
        raise QuotaExceeded(scope, limit)
