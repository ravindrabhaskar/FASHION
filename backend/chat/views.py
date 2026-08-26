"""Chat API: threads, messages, moderation review of flagged messages."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive, IsModerator
from chat.models import Message, Thread
from chat.services import ChatService, message_payload, thread_payload
from core.exceptions import AppError


class ThreadListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        scope = request.query_params.get("scope", "buying")
        qs = (Thread.objects.filter(buyer=request.user) if scope == "buying"
              else Thread.objects.filter(seller_user=request.user))
        return Response({"results": [thread_payload(t) for t in qs[:50]]})

    def post(self, request):
        from django.contrib.auth import get_user_model

        payload = request.data or {}
        User = get_user_model()
        seller = User.objects.filter(id=payload.get("seller_user_id", "")).first()
        if not seller:
            raise AppError("Unknown seller.", code="unknown_seller")
        product = None
        order = None
        quote_request = None
        if payload.get("product_id"):
            from marketplace.models import Product

            product = Product.objects.filter(id=payload["product_id"]).first()
        if payload.get("order_id"):
            from orders.models import Order

            order = Order.objects.filter(id=payload["order_id"]).first()
        if payload.get("quote_request_id"):
            from marketplace.models import QuoteRequest

            quote_request = QuoteRequest.objects.filter(id=payload["quote_request_id"]).first()
        thread = ChatService.get_or_create_thread(
            request.user, seller_user=seller,
            product=product, order=order, quote_request=quote_request,
            subject=str(payload.get("subject", "")),
        )
        detail = thread_payload(thread)
        detail["messages"] = [message_payload(m) for m in thread.messages.all()[:100]]
        return Response(detail, status=status.HTTP_201_CREATED)


class ThreadMessagesView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, thread_id):
        thread = _participant_thread(request, thread_id)
        thread.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
            read_at=timezone.now()
        )
        return Response({
            **thread_payload(thread),
            "messages": [message_payload(m) for m in thread.messages.all()[:200]],
        })

    def post(self, request, thread_id):
        thread = _participant_thread(request, thread_id)
        message = ChatService.send(
            thread, request.user, str((request.data or {}).get("body", ""))
        )
        return Response(message_payload(message), status=status.HTTP_201_CREATED)


class FlaggedMessagesView(APIView):
    """Moderator queue for flagged chat messages (PRD §28 safety)."""

    permission_classes = [IsModerator]

    def get(self, request):
        rows = Message.objects.filter(is_flagged=True).select_related("thread")[:100]
        return Response({
            "count": len(rows),
            "results": [
                {**message_payload(m), "thread_id": str(m.thread_id)}
                for m in rows
            ],
        })


def _participant_thread(request, thread_id) -> Thread:
    thread = get_object_or_404(Thread, id=thread_id)
    if request.user.id not in (thread.buyer_id, thread.seller_user_id) \
            and not request.user.is_superuser and not request.user.is_moderator_level:
        raise AppError("Not part of this conversation.", code="permission_denied")
    return thread
