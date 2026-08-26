from django.urls import path

from notifications import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notifications"),
    path("read", views.NotificationReadView.as_view(), name="notifications-read-all"),
    path("<uuid:notification_id>/read", views.NotificationReadView.as_view(), name="notifications-read"),
    path("devices", views.DeviceTokenView.as_view(), name="notifications-devices"),
]
