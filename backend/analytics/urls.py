from django.urls import path

from analytics import views

urlpatterns = [
    path("trends", views.TrendsView.as_view(), name="trends"),
]
