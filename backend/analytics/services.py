import logging

from core.middleware import request_id_var

logger = logging.getLogger("analytics")


def record_event(*, user=None, name: str, properties: dict | None = None,
                 request=None, source: str = "server", session_key: str = "") -> None:
    """Record a product analytics event. Never raises into the request path."""
    try:
        from analytics.models import AnalyticsEvent

        AnalyticsEvent.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            name=name,
            properties=properties or {},
            source=source if not request else (request.headers.get("X-Client", source) or source),
            request_id=request_id_var.get() or "",
            session_key=session_key or (request.headers.get("X-Session-Key", "") if request else ""),
        )
    except Exception:  # noqa: BLE001 - analytics must never break the API
        logger.exception("analytics event failed: %s", name)
