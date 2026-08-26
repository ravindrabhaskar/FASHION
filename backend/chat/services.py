"""Chat service: buyer↔seller threads with keyword-based moderation flags."""
import re

from analytics.services import record_event
from core.exceptions import AppError
from core.services import get_config
from chat.models import Message, Thread

DEFAULT_FLAGGED_PATTERNS = [
    r"\bwhats\s?app\b", r"\btelegram\b", r"\bpay\s?tm\b", r"\bbank\s+account\b",
    r"\botp\b", r"\bupi\s+(?:id|pin)\b", r"https?://", r"\bcall\s+me\s+(?:at|on)\b",
]


def _flag(body: str) -> str:
    patterns = get_config("chat.flagged_patterns", None) or DEFAULT_FLAGGED_PATTERNS
    for pattern in patterns:
        if re.search(pattern, body.lower()):
            return f"matched {pattern}"
    return ""


class ChatService:
    @staticmethod
    def get_or_create_thread(buyer, *, seller_user, product=None, order=None,
                             quote_request=None, subject: str = "") -> Thread:
        if seller_user.id == buyer.id:
            raise AppError("You can't start a chat with yourself.", code="invalid_thread")
        thread = Thread.objects.filter(
            buyer=buyer, seller_user=seller_user,
            product=product, order=order, quote_request=quote_request,
        ).first()
        if thread:
            return thread
        designer = getattr(seller_user, "designer_profile", None)
        brand = getattr(seller_user, "brand_profile", None)
        thread = Thread.objects.create(
            buyer=buyer, seller_user=seller_user,
            designer=designer if designer else None,
            product=product if product else None,
            order=order if order else None,
            quote_request=quote_request if quote_request else None,
            subject=(subject or (product.title if product else "Order conversation"))[:140],
        )
        record_event(user=buyer, name="chat_started",
                     properties={"thread_id": str(thread.id)})
        return thread

    @staticmethod
    def send(thread: Thread, sender, body: str) -> Message:
        body = body.strip()[:2000]
        if not body:
            raise AppError("Write a message first.", code="empty_message")
        participant = sender.id in (thread.buyer_id, thread.seller_user_id)
        if not participant and not sender.is_superuser:
            raise AppError("Not part of this conversation.", code="permission_denied")
        flag_reason = _flag(body)
        message = Message.objects.create(
            thread=thread, sender=sender, body=body,
            is_flagged=bool(flag_reason), flag_reason=flag_reason[:120],
        )
        other = (thread.seller_user if sender.id == thread.buyer_id else thread.buyer)
        from notifications.services import notify

        notify(other, type="chat", title="New message 💬",
               body=body[:80], data={"thread_id": str(thread.id)})
        record_event(user=sender, name="chat_message_sent",
                     properties={"thread_id": str(thread.id), "flagged": bool(flag_reason)})
        return message


def message_payload(m: Message) -> dict:
    return {
        "id": str(m.id),
        "sender_id": str(m.sender_id),
        "body": m.body,
        "is_flagged": m.is_flagged,
        "created_at": m.created_at,
    }


def thread_payload(t: Thread) -> dict:
    last = t.messages.order_by("-created_at").first()
    return {
        "id": str(t.id),
        "subject": t.subject,
        "buyer_id": str(t.buyer_id),
        "seller_user_id": str(t.seller_user_id),
        "seller_name": (getattr(getattr(t.seller_user, "designer_profile", None), "studio_name", "")
                        or t.seller_user.full_name),
        "unread_for_buyer": t.messages.filter(read_at__isnull=True).exclude(
            sender_id=t.buyer_id).count(),
        "last_message": last.body[:80] if last else "",
        "updated_at": t.updated_at,
    }
