from rest_framework import serializers

from subscriptions.models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    tier_label = serializers.CharField(source="get_tier_display", read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = (
            "code", "name", "tier", "tier_label", "price_inr", "billing_interval_days",
            "features", "is_active",
        )


class CurrentSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ("plan", "status", "current_period_start", "current_period_end",
                  "cancel_at_period_end")
