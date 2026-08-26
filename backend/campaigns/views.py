"""Campaigns API: brand CRUD + creator applications + performance reporting."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from campaigns.models import Application, Campaign
from campaigns.services import CampaignService
from core.exceptions import AppError


def _campaign_payload(c: Campaign) -> dict:
    return {
        "id": str(c.id),
        "title": c.title,
        "brief": c.brief[:280],
        "deliverables": c.deliverables,
        "budget_inr": c.budget_inr,
        "payout_inr": c.payout_inr,
        "min_audience": c.min_audience,
        "status": c.status,
        "brand_name": c.brand.name if c.brand else "",
        "application_count": c.applications.count(),
        "created_at": c.created_at,
    }


class CampaignListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        scope = request.query_params.get("scope", "open")
        qs = (Campaign.objects.filter(status=Campaign.Status.OPEN)
              if scope == "open"
              else Campaign.objects.filter(brand_user=request.user))
        return Response({"count": qs.count(),
                         "results": [_campaign_payload(c) for c in qs[:50]]})

    def post(self, request):
        payload = request.data or {}
        campaign = CampaignService.create(
            request.user,
            title=str(payload.get("title", "")),
            brief=str(payload.get("brief", "")),
            budget_inr=payload.get("budget_inr") or 0,
            deliverables=payload.get("deliverables") or [],
            min_audience=payload.get("min_audience") or 0,
            payout_inr=payload.get("payout_inr"),
        )
        return Response(_campaign_payload(campaign), status=status.HTTP_201_CREATED)


class CampaignDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        payload = _campaign_payload(campaign)
        is_owner = campaign.brand_user_id == request.user.id
        if is_owner:
            payload["applications"] = [
                {
                    "id": str(a.id), "handle": a.creator.handle,
                    "audience_size": a.creator.audience_size,
                    "pitch": a.pitch[:280], "status": a.status,
                    "performance": a.performance,
                }
                for a in campaign.applications.select_related("creator")
            ]
        else:
            mine = request.user.creator_profile.applications.filter(
                campaign=campaign
            ).first() if hasattr(request.user, "creator_profile") else None
            payload["my_application_status"] = mine.status if mine else None
        return Response(payload)

    def patch(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id, brand_user=request.user)
        new_status = str((request.data or {}).get("status", ""))
        valid = dict(Campaign.Status.choices)
        if new_status not in valid:
            raise AppError("Unknown campaign status.", code="invalid_status")
        campaign.status = new_status
        campaign.save(update_fields=["status", "updated_at"])
        return Response(_campaign_payload(campaign))


class ApplyView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, campaign_id):
        campaign = get_object_or_404(Campaign, id=campaign_id)
        profile = getattr(request.user, "creator_profile", None)
        if not profile:
            raise AppError("Register as a creator first.", code="no_creator_profile")
        application = CampaignService.apply(
            profile, campaign, pitch=str((request.data or {}).get("pitch", ""))
        )
        return Response({"id": str(application.id), "status": application.status},
                        status=status.HTTP_201_CREATED)


class ReviewApplicationView(APIView):
    """POST {accept: bool, performance?} — brand decision + performance metrics."""

    permission_classes = [IsAuthenticatedActive]

    def post(self, request, application_id):
        application = get_object_or_404(Application, id=application_id)
        payload = request.data or {}
        application = CampaignService.review(
            request.user, application, accept=bool(payload.get("accept"))
        )
        if payload.get("performance"):
            application.performance = payload["performance"]
            application.save(update_fields=["performance"])
        return Response({"id": str(application.id), "status": application.status})
