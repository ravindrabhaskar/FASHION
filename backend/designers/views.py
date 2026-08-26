"""Designers API: registration, verification (admin), local discovery, storefronts."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive, IsAdmin
from core.models import record_audit
from core.exceptions import AppError
from designers.models import DesignerProfile
from designers.services import DesignerService, designer_payload


class DesignersListView(APIView):
    """GET ?city=&speciality=&q — local designer discovery."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        profiles = DesignerProfile.objects.select_related("user")
        city = request.query_params.get("city", "")
        speciality = request.query_params.get("speciality", "")
        q = request.query_params.get("q", "")
        if city:
            profiles = profiles.filter(city__iexact=city)
        if q:
            from django.db.models import Q

            profiles = profiles.filter(
                Q(studio_name__icontains=q) | Q(tagline__icontains=q) | Q(bio__icontains=q)
            )
        results = [designer_payload(p) for p in profiles]
        if speciality:
            results = [r for r in results if speciality in r["specialities"]]
        return Response({"count": len(results), "results": results})


class MyDesignerView(APIView):
    """GET/PUT own designer profile; POST registers one."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        profile = getattr(request.user, "designer_profile", None)
        if not profile:
            raise AppError("You don't have a designer profile yet.", code="no_designer_profile")
        return Response(designer_payload(profile, detailed=True))

    def post(self, request):
        payload = request.data or {}
        profile = DesignerService.register(
            request.user,
            studio_name=str(payload.get("studio_name", "")),
            slug=str(payload.get("slug", "")).strip().lower().replace(" ", "-"),
            city=str(payload.get("city", "")),
            tagline=str(payload.get("tagline", "")),
            bio=str(payload.get("bio", "")),
            specialities=payload.get("specialities") or [],
            experience_years=payload.get("experience_years"),
        )
        return Response(designer_payload(profile), status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = getattr(request.user, "designer_profile", None)
        if not profile:
            raise AppError("You don't have a designer profile yet.", code="no_designer_profile")
        payload = request.data or {}
        for field in ("studio_name", "tagline", "bio", "city", "instagram"):
            if field in payload:
                setattr(profile, field, str(payload[field])[:400])
        if "specialities" in payload and isinstance(payload["specialities"], list):
            profile.specialities = [s.strip().lower() for s in payload["specialities"]][:10]
        if "is_accepting_custom_requests" in payload:
            profile.is_accepting_custom_requests = bool(payload["is_accepting_custom_requests"])
        profile.save()
        return Response(designer_payload(profile, detailed=True))


class VerifyDesignerView(APIView):
    """POST {verified: true|false} — platform verification (admin only)."""

    permission_classes = [IsAdmin]

    def post(self, request, designer_id):
        profile = get_object_or_404(DesignerProfile, id=designer_id)
        verified = bool((request.data or {}).get("verified"))
        DesignerService.verify(profile, verified=verified)
        record_audit(actor=request.user, action="designer.verify",
                     target_type="DesignerProfile", target_id=str(profile.id),
                     after={"verified": verified})
        return Response(designer_payload(profile))


class DesignerDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, slug: str):
        profile = get_object_or_404(DesignerProfile, slug=slug)
        return Response(designer_payload(profile, detailed=True))
