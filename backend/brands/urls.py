from django.urls import path

from brands import views

urlpatterns = [
    path("", views.BrandsListView.as_view(), name="brands-list"),
    path("me", views.MyBrandView.as_view(), name="brand-me"),
    path("<slug:slug>", views.BrandDetailView.as_view(), name="brand-detail"),
]
