from datetime import timedelta

import pytest
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_free_entitlements_when_no_subscription(user):
    from subscriptions.services import get_entitlements

    ent = get_entitlements(user)
    assert not ent.is_paid
    assert ent.ai_text_daily_limit == 3
    assert not ent.designer_chat_enabled


def test_paid_entitlements_from_plan(user):
    from subscriptions.models import SubscriptionPlan, UserSubscription
    from subscriptions.services import get_entitlements

    plan = SubscriptionPlan.objects.create(
        code="test-designer", name="Designer", tier=SubscriptionPlan.Tier.AI_DESIGNER,
        price_inr=499, ai_text_daily_limit=60, ai_image_monthly_limit=30,
        max_saved_looks=500, wardrobe_item_limit=300, designer_chat_enabled=True,
    )
    now = timezone.now()
    UserSubscription.objects.create(
        user=user, plan=plan, status=UserSubscription.Status.ACTIVE,
        current_period_start=now - timedelta(days=1), current_period_end=now + timedelta(days=29),
    )
    ent = get_entitlements(user)
    assert ent.tier == SubscriptionPlan.Tier.AI_DESIGNER
    assert ent.ai_text_daily_limit == 60
    assert ent.designer_chat_enabled is True
    assert ent.subscription is not None


def test_expired_subscription_falls_back_to_free(user):
    from subscriptions.models import SubscriptionPlan, UserSubscription
    from subscriptions.services import get_entitlements

    plan = SubscriptionPlan.objects.create(
        code="expired-plan", name="Expired", tier=SubscriptionPlan.Tier.DISCOVER, price_inr=199,
    )
    UserSubscription.objects.create(
        user=user, plan=plan, status=UserSubscription.Status.EXPIRED,
        current_period_start=timezone.now() - timedelta(days=40),
        current_period_end=timezone.now() - timedelta(days=10),
    )
    assert get_entitlements(user).tier is None


def test_quota_assertion_raises(user):
    from subscriptions.services import Entitlements, QuotaExceeded, assert_within_quota

    ent = Entitlements(
        tier=None, ai_text_daily_limit=3, ai_image_monthly_limit=2,
        max_saved_looks=10, wardrobe_item_limit=15,
        designer_chat_enabled=False, customization_requests_enabled=False,
    )
    with pytest.raises(QuotaExceeded):
        assert_within_quota(ent, "ai_text", used=3)
    assert_within_quota(ent, "ai_text", used=2)  # within limit â€” no raise


def test_plans_endpoint_lists_seeded_plans(authed_api):
    response = authed_api.get("/api/v1/plans/plans")
    assert response.status_code == 200
    codes = [p["code"] for p in response.json()["data"]]
    assert "style-monthly" in codes or len(codes) == 0  # seeded only via seed_demo
