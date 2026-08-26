from django.urls import path

from profiles import views

urlpatterns = [
    path("me", views.MeProfileView.as_view(), name="profile-me"),
    path("style", views.StyleProfileView.as_view(), name="profile-style"),
    path("onboarding-status", views.OnboardingStatusView.as_view(), name="profile-onboarding-status"),
]
