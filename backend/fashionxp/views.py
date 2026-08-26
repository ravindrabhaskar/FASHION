"""FashionXP + rewards/challenges API surfaces."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from fashionxp.models import (
    Challenge,
    Redemption,
    Reward,
)
from fashionxp import services as xp


def _challenge_status(challenge: Challenge) -> str:
    now = timezone.now()
    if now < challenge.starts_at:
        return "UPCOMING"
    if now > challenge.ends_at:
        return "CLOSED"
    return "LIVE"


class RewardsView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        rewards = Reward.objects.filter(is_active=True)
        return Response({
            "balance": xp.balance(request.user),
            "results": [
                {
                    "code": r.code, "name": r.name, "description": r.description,
                    "cost_xp": r.cost_xp, "stock": r.stock,
                    "partner": r.partner,
                    "affordable": xp.balance(request.user) >= r.cost_xp,
                }
                for r in rewards
            ],
        })


class RedeemView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, reward_code: str):
        reward = Reward.objects.filter(code=reward_code, is_active=True).first()
        if not reward:
            raise AppError("Unknown reward.", code="unknown_reward")
        redemption = xp.redeem_reward(request.user, reward)
        return Response({
            "id": str(redemption.id), "status": redemption.status,
            "cost_xp": redemption.cost_xp, "balance_after": xp.balance(request.user),
        })


class MyRedemptionsView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        rows = request.user.reward_redemptions.select_related("reward")[:50]
        return Response({
            "results": [
                {
                    "id": str(r.id), "reward": r.reward.code, "reward_name": r.reward.name,
                    "cost_xp": r.cost_xp, "status": r.status, "created_at": r.created_at,
                }
                for r in rows
            ]
        })


class ChallengesView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        challenges = Challenge.objects.all()[:30]
        from fashionxp.models import ChallengeEntry

        my_entries = {
            e.challenge_id: e for e in ChallengeEntry.objects.filter(user=request.user)
        }
        return Response({
            "results": [
                {
                    "id": str(c.id), "slug": c.slug, "title": c.title,
                    "description": c.description, "occasion_slug": c.occasion_slug,
                    "hashtag": c.hashtag, "starts_at": c.starts_at, "ends_at": c.ends_at,
                    "xp_reward": c.xp_reward, "status": _challenge_status(c),
                    "enrolled": c.id in my_entries,
                    "my_score": round(my_entries[c.id].score, 1) if c.id in my_entries else None,
                    "entry_count": c.entries.count(),
                }
                for c in challenges
            ]
        })


class ChallengeEnrollView(APIView):
    """POST {post_id?} — join a live challenge with an optional post entry."""

    permission_classes = [IsAuthenticatedActive]

    def post(self, request, challenge_id):
        challenge = get_object_or_404(Challenge, id=challenge_id)
        post = None
        post_id = (request.data or {}).get("post_id")
        if post_id:
            from social.models import Post

            post = Post.objects.filter(id=post_id, user=request.user).first()
            if not post:
                raise AppError("That post isn't yours to enter.", code="invalid_post")
        entry = xp.enroll_challenge(request.user, challenge, post=post)
        return Response({
            "challenge": challenge.slug, "score": round(entry.score, 1),
            "qualified": entry.qualified,
        })


class ChallengeDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, challenge_id):
        challenge = get_object_or_404(Challenge, id=challenge_id)
        board = xp.leaderboard(scope="challenge", challenge_slug=challenge.slug)
        return Response({
            "slug": challenge.slug, "title": challenge.title,
            "description": challenge.description, "hashtag": challenge.hashtag,
            "starts_at": challenge.starts_at, "ends_at": challenge.ends_at,
            "xp_reward": challenge.xp_reward, "status": _challenge_status(challenge),
            "leaderboard": board,
        })
