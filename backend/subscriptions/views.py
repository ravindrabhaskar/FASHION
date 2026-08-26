from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from subscriptions.models import SubscriptionPlan
from subscriptions.serializers import CurrentSubscriptionSerializer, SubscriptionPlanSerializer
from subscriptions.services import get_active_subscription, get_entitlements


class PlansView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class MyEntitlementsView(APIView):
    """Single source of truth the mobile app uses for gating UI."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        ent = get_entitlements(request.user)
        sub = get_active_subscription(request.user)
        return Response({
            "tier": ent.tier,
            "is_paid": ent.is_paid,
            "ai_text_daily_limit": ent.ai_text_daily_limit,
            "ai_image_monthly_limit": ent.ai_image_monthly_limit,
            "max_saved_looks": ent.max_saved_looks,
            "wardrobe_item_limit": ent.wardrobe_item_limit,
            "designer_chat_enabled": ent.designer_chat_enabled,
            "customization_requests_enabled": ent.customization_requests_enabled,
            "subscription": CurrentSubscriptionSerializer(sub).data if sub else None,
        })
