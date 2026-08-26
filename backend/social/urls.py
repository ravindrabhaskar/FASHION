from django.urls import path

from social import views
from fashionxp.views import (
    ChallengeDetailView,
    ChallengeEnrollView,
    ChallengesView,
    MyRedemptionsView,
    RewardsView,
    RedeemView,
)

urlpatterns = [
    path("feed", views.FeedView.as_view(), name="social-feed"),
    path("ai-metadata", views.AiMetadataSuggestView.as_view(), name="social-ai-metadata"),
    path("posts", views.PostListView.as_view(), name="social-posts"),
    path("posts/<uuid:post_id>", views.PostDetailView.as_view(), name="social-post-detail"),
    path("posts/<uuid:post_id>/like", views.LikeToggleView.as_view(), name="social-post-like"),
    path("posts/<uuid:post_id>/save", views.SaveToggleView.as_view(), name="social-post-save"),
    path("posts/<uuid:post_id>/comments", views.CommentListView.as_view(), name="social-post-comments"),
    path("comments/<uuid:comment_id>", views.CommentDeleteView.as_view(), name="social-comment-delete"),
    path("users/<uuid:user_id>/follow", views.FollowToggleView.as_view(), name="social-follow"),
    path("users/<uuid:user_id>/profile", views.PublicProfileView.as_view(), name="social-public-profile"),
    path("reports", views.ReportView.as_view(), name="social-report"),
    path("moderation/reports", views.ModerationQueueView.as_view(), name="moderation-reports"),
    path("moderation/reports/<uuid:report_id>", views.ModerationActionView.as_view(),
         name="moderation-action"),

    # FashionXP surfaces (grouped under /social for client convenience)
    path("xp/me", views.MyXPView.as_view(), name="xp-me"),
    path("xp/leaderboard", views.LeaderboardView.as_view(), name="xp-leaderboard"),
    path("rewards", RewardsView.as_view(), name="xp-rewards"),
    path("rewards/<str:reward_code>/redeem", RedeemView.as_view(), name="xp-redeem"),
    path("rewards/redemptions", MyRedemptionsView.as_view(), name="xp-redemptions"),
    path("challenges", ChallengesView.as_view(), name="xp-challenges"),
    path("challenges/<uuid:challenge_id>/enroll", ChallengeEnrollView.as_view(),
         name="xp-challenge-enroll"),
    path("challenges/<uuid:challenge_id>", ChallengeDetailView.as_view(), name="xp-challenge-detail"),
]
