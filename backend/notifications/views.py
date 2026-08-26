"""Notifications API: inbox, unread count, mark-read, device token registration."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from notifications.models import DeviceToken, Notification
from notifications.services import unread_count


class NotificationListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        rows = Notification.objects.filter(user=request.user)[:50]
        return Response({
            "unread": unread_count(request.user),
            "results": [_payload(n) for n in rows],
        })


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, notification_id=None):
        if notification_id:
            row = get_object_or_404(Notification, id=notification_id, user=request.user)
            row.read_at = timezone.now()
            row.save(update_fields=["read_at"])
            return Response(_payload(row))
        from notifications.services import mark_all_read

        updated = mark_all_read(request.user)
        return Response({"marked_read": updated})


class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request):
        token = str((request.data or {}).get("token", "")).strip()
        platform = str((request.data or {}).get("platform", "android")).lower()
        if not token or len(token) > 255:
            raise AppError("A valid push token is required.", code="invalid_token")
        if platform not in DeviceToken.Platform.values:
            raise AppError("Unknown platform.", code="invalid_platform")
        obj, _ = DeviceToken.objects.update_or_create(
            token=token,
            defaults={"user": request.user, "platform": platform, "is_active": True},
        )
        return Response({"registered": True, "id": str(obj.id)}, status=status.HTTP_201_CREATED)


def _payload(n: Notification) -> dict:
    return {
        "id": str(n.id),
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "data": n.data,
        "read_at": n.read_at,
        "created_at": n.created_at,
    }
