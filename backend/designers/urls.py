from django.urls import path

from designers import views

urlpatterns = [
    path("", views.DesignersListView.as_view(), name="designers-list"),
    path("me", views.MyDesignerView.as_view(), name="designer-me"),
    path("<slug:slug>", views.DesignerDetailView.as_view(), name="designer-detail"),
    path("<uuid:designer_id>/verify", views.VerifyDesignerView.as_view(), name="designer-verify"),
]
