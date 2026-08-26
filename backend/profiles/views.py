"""Profile + style profile APIs, including progressive onboarding."""
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from analytics.services import record_event
from profiles.models import StyleProfile
from profiles.serializers import StyleProfileSerializer, UserProfileSerializer


class MeProfileView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        return Response(UserProfileSerializer(request.user.profile).data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StyleProfileView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        return Response(StyleProfileSerializer(request.user.style_profile).data)

    def put(self, request):
        """Full update — used at the end of onboarding."""
        serializer = StyleProfileSerializer(request.user.style_profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.completion_cache = instance.compute_completion()
        instance.save(update_fields=["completion_cache", "updated_at"])
        self._mark_onboarded(request)
        return Response(StyleProfileSerializer(instance).data)

    def patch(self, request):
        """Progressive profiling: client may send one attribute at a time."""
        serializer = StyleProfileSerializer(request.user.style_profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.completion_cache = instance.compute_completion()
        instance.save(update_fields=["completion_cache", "updated_at"])
        self._mark_onboarded(request)
        return Response(StyleProfileSerializer(instance).data)

    @staticmethod
    def _mark_onboarded(request) -> None:
        user = request.user
        if user.onboarding_completed_at is None:
            user.onboarding_completed_at = timezone.now()
            user.save(update_fields=["onboarding_completed_at", "updated_at"])
            record_event(user=user, name="onboarding_completed",
                         properties={"style_completion": user.style_profile.compute_completion()},
                         request=request)


class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        sp: StyleProfile = request.user.style_profile
        steps = [
            {"key": "basic_profile", "done": bool(request.user.full_name)},
            {"key": "styles", "done": bool(sp.preferred_styles)},
            {"key": "colors", "done": bool(sp.favorite_colors or sp.avoided_colors)},
            {"key": "fit", "done": bool(sp.fit_preference)},
            {"key": "budget", "done": sp.budget_max is not None},
            {"key": "occasions", "done": bool(sp.common_occasions)},
        ]
        return Response({
            "completed": request.user.onboarding_completed_at is not None,
            "completion_percent": sp.compute_completion(),
            "steps": steps,
        })
