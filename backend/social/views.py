"""Social API: feed, posts, interactions, profiles, moderation queue."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive, IsModerator
from analytics.services import record_event
from core.exceptions import AppError
from fashionxp import services as xp
from social.models import Comment, Post, Report, SavedPost
from social.services import (
    SocialService,
    comment_payload,
    _post_payload,
)
from wardrobe.views import _validate_image_upload

User = get_user_model()


class FeedView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get("page", "1")))
        except ValueError:
            page = 1
        data = SocialService.feed(request.user, page=page)
        return Response(data)


class AiMetadataSuggestView(APIView):
    """POST {occasion?, seed?} — AI caption/tags for the composer (editable)."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        payload = request.data or {}
        suggestion = SocialService.suggest_metadata(
            request.user,
            caption_seed=str(payload.get("seed", ""))[:300],
            occasion=str(payload.get("occasion", "")),
        )
        return Response(suggestion)


class PostListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        """GET ?user_id=&saved=true — grid lists."""
        posts = Post.objects.filter(status=Post.Status.PUBLISHED).select_related("user")
        user_id = request.query_params.get("user_id", "")
        if user_id:
            posts = posts.filter(user_id=user_id)
        if request.query_params.get("saved") == "true":
            saved_ids = SavedPost.objects.filter(user=request.user).values_list("post_id", flat=True)
            posts = posts.filter(id__in=saved_ids)
        limit = min(int(request.query_params.get("limit", "24") or 24), 60)
        return Response({"count": posts.count(),
                         "results": [_post_payload(p) for p in posts[:limit]]})

    def post(self, request):
        photo = request.FILES.get("photo")
        image_bytes = _validate_image_upload(photo) if photo else None
        outfit_id = (request.data or {}).get("outfit_id")
        source_outfit = None
        if outfit_id:
            from fashion.models import GeneratedOutfit

            source_outfit = GeneratedOutfit.objects.filter(
                id=outfit_id, user=request.user
            ).first()
        raw_tags = (request.data or {}).get("item_tags")
        item_tags = raw_tags if isinstance(raw_tags, list) else []
        post = SocialService.create_post(
            request.user,
            caption=str((request.data or {}).get("caption", ""))[:1000],
            occasion=str((request.data or {}).get("occasion", "")),
            image_bytes=image_bytes,
            filename=getattr(photo, "name", "") or "post.jpg",
            source_outfit=source_outfit,
            item_tags=item_tags,
        )
        return Response(_post_payload(post), status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        return Response(_post_payload(post))

    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        SocialService.delete_post(request.user, post)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LikeToggleView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        liked = SocialService.toggle_like(request.user, post)
        post.refresh_from_db()
        return Response({"liked": liked, "like_count": post.like_count})


class SaveToggleView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        saved = SocialService.toggle_save(request.user, post)
        return Response({"saved": saved})


class CommentListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        comments = post.comments.filter(is_hidden=False)[:100]
        return Response({"results": [comment_payload(c) for c in comments]})

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
        text = str((request.data or {}).get("text", ""))
        comment = SocialService.add_comment(request.user, post, text)
        return Response(comment_payload(comment), status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        is_owner = comment.user_id == request.user.id
        is_post_owner = comment.post.user_id == request.user.id
        can_moderate = request.user.is_moderator_level or request.user.is_superuser
        if not (is_owner or is_post_owner or can_moderate):
            raise AppError("You can't remove this comment.", code="permission_denied")
        comment.is_hidden = True
        comment.save(update_fields=["is_hidden"])
        from django.db.models import F

        Post.objects.filter(pk=comment.post_id).update(
            comment_count=F("comment_count") - 1
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowToggleView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, user_id):
        target = get_object_or_404(User, id=user_id)
        following = SocialService.toggle_follow(request.user, target)
        return Response({"following": following})


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, user_id):
        target = get_object_or_404(User, id=user_id)
        return Response(SocialService.public_profile(target, viewer=request.user))


class ReportView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request):
        payload = request.data or {}
        report = SocialService.report(
            request.user,
            target_type=str(payload.get("target_type", "")),
            target_id=str(payload.get("target_id", "")),
            reason=str(payload.get("reason", "")),
            details=str(payload.get("details", "")),
        )
        return Response({"id": str(report.id), "status": report.status},
                        status=status.HTTP_201_CREATED)


class ModerationQueueView(APIView):
    permission_classes = [IsModerator]

    def get(self, request):
        rows = Report.objects.filter(status=Report.Status.OPEN)[:100]
        return Response({
            "count": len(rows),
            "results": [
                {
                    "id": str(r.id), "reporter_id": str(r.reporter_id),
                    "target_type": r.target_type, "target_id": r.target_id,
                    "reason": r.reason, "details": r.details,
                    "status": r.status, "created_at": r.created_at,
                }
                for r in rows
            ],
        })


class ModerationActionView(APIView):
    """POST {action: dismiss|remove_post} on an open report."""

    permission_classes = [IsModerator]

    def post(self, request, report_id):
        report = get_object_or_404(Report, id=report_id)
        action = str((request.data or {}).get("action", ""))
        if action == "dismiss":
            report.status = Report.Status.DISMISSED
        elif action == "remove_post":
            if report.target_type != Report.TargetType.POST:
                raise AppError("This report isn't about a post.", code="invalid_action")
            Post.objects.filter(id=report.target_id).update(
                status=Post.Status.REMOVED
            )
            report.status = Report.Status.ACTIONED
            record_event(name="moderation_removed",
                         properties={"post_id": report.target_id})
        else:
            raise AppError("Unknown moderation action.", code="invalid_action")
        report.resolved_by = request.user
        report.save(update_fields=["status", "resolved_by"])
        from core.models import record_audit

        record_audit(actor=request.user, action=f"moderation.{action}",
                     target_type="Report", target_id=str(report.id))
        return Response({"id": str(report.id), "status": report.status})


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        scope = request.query_params.get("scope", "global")
        data = xp.leaderboard(
            scope=scope,
            city=request.query_params.get("city", ""),
            challenge_slug=request.query_params.get("challenge", ""),
            limit=20,
        )
        return Response({"scope": scope, "results": data})


class MyXPView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        total = xp.balance(request.user)
        level = xp.level_for(total)
        badges = [
            {"code": ub.badge.code, "name": ub.badge.name, "icon": ub.badge.icon,
             "awarded_at": ub.awarded_at}
            for ub in request.user.badges.select_related("badge")[:30]
        ]
        recent = [
            {"amount": t.amount, "reason": t.reason, "balance_after": t.balance_after,
             "created_at": t.created_at}
            for t in request.user.xp_transactions.all()[:20]
        ]
        return Response({
            "total_xp": total,
            "level": level.name,
            "level_number": level.level,
            "next_threshold": level.next_threshold,
            "progress_percent": level.progress_percent,
            "earned_today": xp.earned_today(request.user),
            "daily_cap": xp.daily_cap(),
            "badges": badges,
            "recent_transactions": recent,
        })
