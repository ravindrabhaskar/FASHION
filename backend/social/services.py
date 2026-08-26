"""Social domain services: posts, interactions, deterministic feed, moderation.

Feed ranking is deterministic and explainable (PRD §17): follow boost + city
boost + engagement + recency decay. No ML until volume justifies it.
"""
from django.db.models import F
from django.utils import timezone

from analytics.services import record_event
from core.exceptions import AppError
from core.services import is_enabled
from fashion.registry import get_occasion
from social.models import (
    Comment,
    Follow,
    Like,
    Post,
    PostItemTag,
    Report,
    SavedPost,
)

MAX_FEED_POOL = 300


def _require_social_enabled() -> None:
    if not is_enabled("social_feed", default=True):
        raise AppError("The social feed is coming soon.", code="feature_disabled")


class SocialService:
    # ---- Posts -----------------------------------------------------------

    @staticmethod
    def create_post(user, *, caption: str = "", occasion: str = "", image_bytes: bytes | None = None,
                    filename: str = "post.jpg", source_outfit=None,
                    item_tags: list[dict] | None = None) -> Post:
        _require_social_enabled()
        if not image_bytes and source_outfit is None:
            raise AppError("Add a photo or pick one of your saved looks to share.",
                           code="post_content_required")
        if occasion and not get_occasion(occasion):
            raise AppError("Unknown occasion.", code="unknown_occasion")

        post = Post.objects.create(
            user=user,
            caption=caption[:1000],
            occasion=occasion or "",
            source_outfit=source_outfit,
            ai_metadata=(source_outfit.recommendation.get("headline", "") if source_outfit else ""),
            city_snapshot=getattr(getattr(user, "profile", None), "city", "") or "",
        )
        if image_bytes:
            from wardrobe.services import _content_file, _ext_for

            post.image.save(f"posts/{post.id}{_ext_for(filename)}", _content_file(image_bytes))

        for i, tag in enumerate((item_tags or [])[:8]):
            PostItemTag.objects.create(
                post=post,
                label=str(tag.get("label", ""))[:120] or f"Piece {i + 1}",
                wardrobe_item_id=tag.get("wardrobe_item_id") or None,
                position=i,
            )

        from fashionxp.services import award

        award(user, "post_created", ref_type="post", ref_id=str(post.id))
        record_event(user=user, name="post_published",
                     properties={"post_id": str(post.id), "occasion": occasion,
                                 "has_outfit": source_outfit is not None})
        return post

    @staticmethod
    def suggest_metadata(user, *, caption_seed: str = "", occasion: str = "") -> dict:
        """AI-suggested caption + tags for the composer; fully editable client-side."""
        from ai import orchestrator

        result = orchestrator.designer_turn(
            user=user,
            conversation_history=[],
            message=f"Write a short social caption (max 2 lines) for sharing this look."
                    f" Occasion: {occasion or 'casual'}. Context: {caption_seed or 'my latest look'}",
            current_design=None,
        )
        tags = ["ootd", "fashionxp"]
        if occasion:
            tags.append(occasion.replace("-", ""))
        return {"suggested_caption": result.reply.strip(), "suggested_tags": tags}

    @staticmethod
    def delete_post(user, post: Post) -> None:
        if post.user_id != user.id:
            raise AppError("You can only delete your own posts.", code="not_post_owner")
        post.delete()

    # ---- Interactions ------------------------------------------------------

    @staticmethod
    def toggle_like(user, post: Post) -> bool:
        existing = Like.objects.filter(user=user, post=post).first()
        if existing:
            existing.delete()
            Post.objects.filter(pk=post.pk).update(like_count=F("like_count") - 1)
            return False
        Like.objects.create(user=user, post=post)
        Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)
        if post.like_count <= 50:  # anti-abuse: XP only for the first 50 likes per post
            from fashionxp.services import award

            award(post.user, "like_received", ref_type="post", ref_id=str(post.id))
        if post.user_id != user.id:
            from notifications.services import notify

            notify(post.user, type="social", title="Someone loved your look ❤",
                   body=post.caption[:80] or "Your style is getting attention!",
                   data={"post_id": str(post.id)})
        record_event(user=user, name="post_liked", properties={"post_id": str(post.id)})
        return True

    @staticmethod
    def add_comment(user, post: Post, text: str) -> Comment:
        text = text.strip()[:500]
        if not text:
            raise AppError("Write something first.", code="empty_comment")
        comment = Comment.objects.create(post=post, user=user, text=text)
        Post.objects.filter(pk=post.pk).update(comment_count=F("comment_count") + 1)
        from fashionxp.services import award

        award(user, "comment_written", ref_type="post", ref_id=str(post.id))
        if post.user_id != user.id:
            from notifications.services import notify

            notify(post.user, type="social", title="New comment on your look 💬",
                   body=text[:80], data={"post_id": str(post.id), "comment_id": str(comment.id)})
        record_event(user=user, name="post_commented", properties={"post_id": str(post.id)})
        return comment

    @staticmethod
    def toggle_save(user, post: Post) -> bool:
        existing = SavedPost.objects.filter(user=user, post=post).first()
        if existing:
            existing.delete()
            return False
        SavedPost.objects.create(user=user, post=post)
        record_event(user=user, name="post_saved", properties={"post_id": str(post.id)})
        return True

    @staticmethod
    def toggle_follow(user, target) -> bool:
        if target.id == user.id:
            raise AppError("You can't follow yourself.", code="invalid_follow")
        existing = Follow.objects.filter(follower=user, followed_to=target).first()
        if existing:
            existing.delete()
            return False
        Follow.objects.create(follower=user, followed_to=target)
        from fashionxp.services import award

        award(target, "follow_received", ref_type="user", ref_id=str(user.id))
        from notifications.services import notify

        notify(target, type="social", title="You have a new follower ✦",
               body=f"{getattr(user, 'full_name', 'Someone')} started following you.",
               data={"user_id": str(user.id)})
        record_event(user=user, name="user_followed",
                     properties={"target_id": str(target.id)})
        return True

    @staticmethod
    def report(user, *, target_type: str, target_id: str, reason: str,
               details: str = "") -> Report:
        valid_targets = dict(Report.TargetType.choices).keys()
        valid_reasons = dict(Report.Reason.choices).keys()
        if target_type not in valid_targets:
            raise AppError("Unknown report target.", code="invalid_report_target")
        if reason not in valid_reasons:
            raise AppError("Unknown report reason.", code="invalid_report_reason")
        report = Report.objects.create(
            reporter=user, target_type=target_type, target_id=target_id[:64],
            reason=reason, details=details[:500],
        )
        record_event(user=user, name="content_reported",
                     properties={"target_type": target_type, "reason": reason})
        return report

    # ---- Feed --------------------------------------------------------------

    @staticmethod
    def feed(user, *, page: int = 1, page_size: int = 10) -> dict:
        _require_social_enabled()
        now = timezone.now()
        following_ids = set(
            Follow.objects.filter(follower=user).values_list("followed_to_id", flat=True)
        )
        my_city = getattr(getattr(user, "profile", None), "city", "") or ""

        pool = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .select_related("user", "user__profile", "source_outfit")
            .prefetch_related("item_tags")
            .order_by("-created_at")[:MAX_FEED_POOL]
        )
        liked_ids = set(Like.objects.filter(user=user, post__in=[p.id for p in pool])
                        .values_list("post_id", flat=True))
        saved_ids = set(SavedPost.objects.filter(user=user, post__in=[p.id for p in pool])
                        .values_list("post_id", flat=True))

        scored = []
        for p in pool:
            days_old = max(0.0, (now - p.created_at).total_seconds() / 86400)
            score = (
                (30 if p.user_id in following_ids else 0)
                + (20 if my_city and p.city_snapshot.lower() == my_city.lower() else 0)
                + min(p.like_count * 3 + p.comment_count * 5, 40)
                + max(0, 15 - days_old * 2)
            )
            scored.append((score, p))
        scored.sort(key=lambda pair: (-pair[0], -pair[1].created_at.timestamp()))

        total = len(scored)
        start = (page - 1) * page_size
        rows = scored[start:start + page_size]
        return {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [
                {**_post_payload(p),
                 "score": round(s, 1),
                 "liked_by_me": p.id in liked_ids,
                 "saved_by_me": p.id in saved_ids}
                for s, p in rows
            ],
        }

    @staticmethod
    def public_profile(target, *, viewer=None) -> dict:
        followers = Follow.objects.filter(followed_to=target).count()
        following_n = Follow.objects.filter(follower=target).count()
        posts = Post.objects.filter(user=target, status=Post.Status.PUBLISHED)[:12]
        is_following = bool(
            viewer and Follow.objects.filter(follower=viewer, followed_to=target).exists()
        )
        xp_summary = {}
        try:
            from fashionxp import services as xp

            total = xp.balance(target)
            level = xp.level_for(total)
            xp_summary = {"total_xp": total, "level": level.name,
                          "level_progress": level.progress_percent}
        except Exception:  # noqa: BLE001
            pass
        return {
            "user_id": str(target.id),
            "display_name": (getattr(getattr(target, "profile", None), "display_name", "")
                             or target.full_name),
            "city": getattr(getattr(target, "profile", None), "city", ""),
            "followers": followers,
            "following": following_n,
            "is_following": is_following,
            **xp_summary,
            "recent_posts": [_post_payload(p) for p in posts],
        }


# ---- payload helpers ---------------------------------------------------------


def post_image_url(post: Post) -> str:
    if post.image:
        url = post.image.url if hasattr(post.image, "url") else str(post.image)
    elif post.source_outfit and post.source_outfit.image:
        url = post.source_outfit.image.url
    else:
        return ""
    if url.startswith("/"):
        from django.conf import settings as dj_settings

        url = f"http://localhost:8000{url}" if dj_settings.DEBUG else url
    return url


def _post_payload(post: Post) -> dict:
    return {
        "id": str(post.id),
        "user_id": str(post.user_id),
        "user_name": (getattr(getattr(post.user, "profile", None), "display_name", "")
                      or post.user.full_name),
        "caption": post.caption,
        "occasion": post.occasion,
        "image": post_image_url(post),
        "outfit_id": str(post.source_outfit_id) if post.source_outfit_id else None,
        "ai_metadata": post.ai_metadata,
        "item_tags": [
            {
                "id": str(t.id),
                "label": t.label,
                "wardrobe_item_id": str(t.wardrobe_item_id) if t.wardrobe_item_id else None,
                "product_id": str(t.product_id) if t.product_id else None,
                "position": t.position,
            }
            for t in post.item_tags.all()
        ],
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "created_at": post.created_at,
    }


def comment_payload(comment: Comment) -> dict:
    return {
        "id": str(comment.id),
        "post_id": str(comment.post_id),
        "user_id": str(comment.user_id),
        "user_name": (getattr(getattr(comment.user, "profile", None), "display_name", "")
                      or comment.user.full_name),
        "text": comment.text,
        "is_hidden": comment.is_hidden,
        "created_at": comment.created_at,
    }
