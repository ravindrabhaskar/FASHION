from django.urls import path

from creators import views

urlpatterns = [
    path("me", views.MyCreatorView.as_view(), name="creator-me"),
    path("eligibility", views.CreatorEligibilityView.as_view(), name="creator-eligibility"),
    path("portfolio", views.PortfolioView.as_view(), name="creator-portfolio"),
]
