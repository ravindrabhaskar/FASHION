from django.urls import path

from subscriptions import views

urlpatterns = [
    path("plans", views.PlansView.as_view(), name="plans"),
    path("entitlements", views.MyEntitlementsView.as_view(), name="my-entitlements"),
]
