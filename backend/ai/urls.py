from django.urls import path

from ai import views

urlpatterns = [
    path("transcribe", views.TranscribeView.as_view(), name="ai-transcribe"),
    path("translate", views.TranslateView.as_view(), name="ai-translate"),
]
