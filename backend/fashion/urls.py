from django.urls import path

from fashion import views

urlpatterns = [
    path("occasions", views.OccasionsView.as_view(), name="fashion-occasions"),
    path("analyze", views.AnalyzePhotoView.as_view(), name="fashion-analyze"),
    path("recommend", views.RecommendOutfitView.as_view(), name="fashion-recommend"),
    path("outfits/generate", views.GenerateOutfitView.as_view(), name="outfit-generate"),
    path("outfits", views.OutfitListView.as_view(), name="outfit-list"),
    path("outfits/<uuid:outfit_id>", views.OutfitDetailView.as_view(), name="outfit-detail"),
    path("outfits/<uuid:outfit_id>/save", views.SaveOutfitView.as_view(), name="outfit-save"),
    path("designer/conversations", views.ConversationListView.as_view(), name="designer-conversations"),
    path(
        "designer/conversations/<uuid:conversation_id>",
        views.ConversationDetailView.as_view(),
        name="designer-conversation-detail",
    ),
    path(
        "designer/conversations/<uuid:conversation_id>/messages",
        views.ConversationMessageView.as_view(),
        name="designer-conversation-message",
    ),
    path(
        "designer/conversations/<uuid:conversation_id>/materialize",
        views.MaterializeLookView.as_view(),
        name="designer-materialize",
    ),
    path("outfits/<uuid:outfit_id>/tryon", views.TryOnView.as_view(), name="outfit-tryon"),
    path("trends", views.TrendsView.as_view(), name="fashion-trends"),
    path("i18n/strings", views.I18nStringsView.as_view(), name="fashion-i18n-strings"),
]
