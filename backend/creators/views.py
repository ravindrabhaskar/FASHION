"""Creators API: registration, profile, portfolio, platform analytics."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from creators.services import CreatorService, creator_payload, eligibility_thresholds


class MyCreatorView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        from creators.models import CreatorProfile

        try:
            profile = request.user.creator_profile
        except CreatorProfile.DoesNotExist as exc:
            raise AppError("You're not a creator yet.", code="no_creator_profile") from exc
        return Response(creator_payload(profile))

    def post(self, request):
        payload = request.data or {}
        profile = CreatorService.register(
            request.user,
            handle=str(payload.get("handle", "")),
            niche=str(payload.get("niche", "")),
            platforms=payload.get("platforms") or {},
            audience_size=payload.get("audience_size") or 0,
        )
        return Response(creator_payload(profile), status=status.HTTP_201_CREATED)

    def patch(self, request):
        from creators.models import CreatorProfile

        try:
            profile = request.user.creator_profile
        except CreatorProfile.DoesNotExist as exc:
            raise AppError("You're not a creator yet.", code="no_creator_profile") from exc
        payload = request.data or {}
        for field in ("niche",):
            if field in payload:
                setattr(profile, field, str(payload[field])[:80])
        if "audience_size" in payload:
            profile.audience_size = max(0, int(payload["audience_size"] or 0))
        if "platforms" in payload and isinstance(payload["platforms"], dict):
            profile.platforms = {str(k): str(v) for k, v in list(payload["platforms"].items())[:8]}
        profile.save()
        CreatorService.refresh_eligibility(profile)
        return Response(creator_payload(profile))


class CreatorEligibilityView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        thresholds = eligibility_thresholds()
        posts_count = request.user.posts.filter(status="PUBLISHED").count()
        return Response({
            **thresholds,
            "posts_published": posts_count,
            "qualifies": posts_count >= thresholds["min_posts"],
        })


class PortfolioView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request):
        from creators.models import CreatorProfile, PortfolioItem

        try:
            profile = request.user.creator_profile
        except CreatorProfile.DoesNotExist as exc:
            raise AppError("You're not a creator yet.", code="no_creator_profile") from exc
        payload = request.data or {}
        item = PortfolioItem.objects.create(
            creator=profile,
            title=str(payload.get("title", ""))[:140],
            media_url=str(payload.get("media_url", "")),
            metrics=payload.get("metrics") or {},
        )
        return Response({"id": str(item.id), "title": item.title},
                        status=status.HTTP_201_CREATED)
