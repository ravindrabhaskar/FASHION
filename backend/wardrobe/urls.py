from django.urls import path

from wardrobe import views

urlpatterns = [
    path("items", views.WardrobeItemListView.as_view(), name="wardrobe-items"),
    path("items/<uuid:item_id>", views.WardrobeItemDetailView.as_view(), name="wardrobe-item-detail"),
    path("items/<uuid:item_id>/worn", views.WardrobeItemWornView.as_view(), name="wardrobe-item-worn"),
    path("closet/recommend", views.ClosetRecommendView.as_view(), name="wardrobe-closet-recommend"),
    path("daily", views.DailySuggestionView.as_view(), name="wardrobe-daily"),
]
