"""Trends aggregation API — deterministic on-platform analytics (PRD §43)."""
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive


class TrendsView(APIView):
    """GET /api/v1/trends?city=&days=30 — what the community is wearing right now."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        from social.models import Post
        from wardrobe.models import WardrobeItem

        try:
            days = max(7, min(int(request.query_params.get("days", "30")), 90))
        except ValueError:
            days = 30
        city = request.query_params.get("city", "").strip()
        since = timezone.now() - timezone.timedelta(days=days)

        posts = Post.objects.filter(status="PUBLISHED", created_at__gte=since)
        items = WardrobeItem.objects.filter(archived=False)
        if city:
            posts = posts.filter(user__profile__city__iexact=city)
            items = items.filter(user__profile__city__iexact=city)

        top_occasions = list(
            posts.exclude(occasion="").values("occasion")
            .annotate(n=Count("id")).order_by("-n")[:5]
        )
        colors: dict[str, int] = {}
        for row in items.values_list("color_primary", flat=True):
            if row:
                colors[row] = colors.get(row, 0) + 1
        fabrics: dict[str, int] = {}
        for row in items.values_list("fabric", flat=True):
            if row:
                fabrics[row] = fabrics.get(row, 0) + 1

        return Response({
            "window_days": days,
            "city": city,
            "trending_occasions": [
                {"occasion": r["occasion"], "posts": r["n"]} for r in top_occasions
            ],
            "trending_colors": sorted(colors.items(), key=lambda kv: -kv[1])[:6],
            "trending_fabrics": sorted(fabrics.items(), key=lambda kv: -kv[1])[:6],
            "post_volume": posts.count(),
        })
