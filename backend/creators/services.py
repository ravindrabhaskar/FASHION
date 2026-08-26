"""Creator services: registration, eligibility, portfolio, analytics."""
from django.utils import timezone

from analytics.services import record_event
from core.exceptions import AppError
from core.services import get_config
from creators.models import CreatorProfile, PortfolioItem


def eligibility_thresholds() -> dict:
    return {
        "min_audience": int(get_config("creators.min_audience", 1000) or 0),
        "min_posts": int(get_config("creators.min_posts", 5) or 0),
    }


class CreatorService:
    @staticmethod
    def register(user, *, handle: str, niche: str = "", platforms=None,
                 audience_size: int = 0) -> CreatorProfile:
        handle = handle.strip().lower().lstrip("@")
        if not handle:
            raise AppError("Pick a creator handle.", code="validation_error")
        if CreatorProfile.objects.filter(handle=handle).exclude(user=user).exists():
            raise AppError("That handle is taken.", code="handle_taken")
        profile, _ = CreatorProfile.objects.update_or_create(
            user=user,
            defaults={
                "handle": handle[:50],
                "niche": niche[:80],
                "platforms": platforms or {},
                "audience_size": max(0, int(audience_size or 0)),
            },
        )
        CreatorService.refresh_eligibility(profile)
        record_event(user=user, name="creator_registered",
                     properties={"creator_id": str(profile.id)})
        return profile

    @staticmethod
    def refresh_eligibility(profile: CreatorProfile) -> CreatorProfile:
        thresholds = eligibility_thresholds()
        posts_count = profile.user.posts.filter(status="PUBLISHED").count()
        profile.is_eligible = (
            profile.audience_size >= thresholds["min_audience"]
            and posts_count >= thresholds["min_posts"]
        )
        profile.eligibility_checked_at = timezone.now()
        profile.save(update_fields=["is_eligible", "eligibility_checked_at", "updated_at"])
        return profile

    @staticmethod
    def refresh_stats(profile: CreatorProfile) -> CreatorProfile:
        """Deterministic platform analytics from on-platform activity."""
        user = profile.user
        posts = list(user.posts.filter(status="PUBLISHED")[:50])
        likes = sum(p.like_count for p in posts)
        comments = sum(p.comment_count for p in posts)
        saves = sum(p.saves.count() for p in posts)
        profile.stats = {
            "posts_published": len(posts),
            "likes_received": likes,
            "comments_received": comments,
            "saves_received": saves,
            "engagement_rate": round((likes + comments + saves) / max(len(posts), 1), 2),
        }
        profile.stats_updated_at = timezone.now()
        profile.save(update_fields=["stats", "stats_updated_at"])
        return profile


def creator_payload(profile: CreatorProfile) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "handle": profile.handle,
        "niche": profile.niche,
        "audience_size": profile.audience_size,
        "is_eligible": profile.is_eligible,
        "stats": profile.stats,
        "portfolio": [
            {
                "id": str(item.id), "title": item.title,
                "media_url": item.media_url,
                "metrics": item.metrics,
            }
            for item in profile.portfolio_items.all()[:12]
        ],
    }
