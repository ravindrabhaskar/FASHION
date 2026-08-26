from django.urls import path

from chat import views

urlpatterns = [
    path("", views.ThreadListView.as_view(), name="chat-threads"),
    path("<uuid:thread_id>/messages", views.ThreadMessagesView.as_view(),
         name="chat-thread-messages"),
    path("moderation/flagged", views.FlaggedMessagesView.as_view(), name="chat-flagged"),
]
