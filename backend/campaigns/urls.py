from django.urls import path

from campaigns import views

urlpatterns = [
    path("", views.CampaignListView.as_view(), name="campaigns"),
    path("<uuid:campaign_id>", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path("<uuid:campaign_id>/apply", views.ApplyView.as_view(), name="campaign-apply"),
    path("applications/<uuid:application_id>/review", views.ReviewApplicationView.as_view(),
         name="campaign-application-review"),
]
