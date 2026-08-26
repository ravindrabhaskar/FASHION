"""Notification service: in-app inbox + best-effort push dispatch.

Push delivery is provider-abstracted (PUSH_PROVIDER setting): 'console' logs,
'fcm' posts to the FCM legacy endpoint when FCM_SERVER_KEY is configured.
Failures never break the calling flow.
"""
import logging

import httpx
from django.conf import settings
from django.utils import timezone

from notifications.models import DeviceToken, Notification

logger = logging.getLogger(__name__)


def notify(user, *, type: str, title: str, body: str = "", data: dict | None = None) -> Notification | None:
    if getattr(user, "is_authenticated", False) is False and not getattr(user, "id", None):
        return None
    row = Notification.objects.create(
        user=user, type=type, title=title[:140], body=(body or "")[:300], data=data or {}
    )
    _push(user, title=title[:140], body=(body or "")[:300], data={**(data or {}), "type": type})
    return row


def _push(user, *, title: str, body: str, data: dict) -> None:
    tokens = list(DeviceToken.objects.filter(user=user, is_active=True))
    if not tokens:
        return
    provider = getattr(settings, "PUSH_PROVIDER", "console")
    for t in tokens:
        try:
            if provider == "fcm" and getattr(settings, "FCM_SERVER_KEY", ""):
                _fcm_send(t.token, title, body, data)
            else:
                logger.info("PUSH[%s] %s → %s… (%s)", provider, title, t.token[:12], data.get("type"))
        except Exception:  # noqa: BLE001
            logger.exception("push send failed")


def _fcm_send(token: str, title: str, body: str, data: dict) -> None:
    response = httpx.post(
        "https://fcm.googleapis.com/fcm/send",
        headers={"Authorization": f"key={settings.FCM_SERVER_KEY}"},
        json={
            "to": token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in data.items()},
        },
        timeout=5,
    )
    if response.status_code == 404:
        DeviceToken.objects.filter(token=token).update(is_active=False)


def unread_count(user) -> int:
    return Notification.objects.filter(user=user, read_at__isnull=True).count()


def mark_all_read(user) -> int:
    return Notification.objects.filter(
        user=user, read_at__isnull=True
    ).update(read_at=timezone.now())
