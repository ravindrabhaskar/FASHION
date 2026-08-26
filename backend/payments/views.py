"""Payments API: initiate, confirm (mock), provider webhooks."""
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from orders.models import Order
from payments.models import Payment
from payments.services import PaymentService


class PayView(APIView):
    """POST {order_id, provider?, idempotency_key?} → payment attempt."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"  # reuse the stricter bucket for money-adjacent calls

    def post(self, request):
        payload = request.data or {}
        order = get_object_or_404(Order, id=payload.get("order_id", ""), customer=request.user)
        payment = PaymentService.initiate(
            request.user, order,
            provider=str(payload.get("provider", "")),
            idempotency_key=str(payload.get("idempotency_key", "")),
        )
        return Response({
            "payment_id": str(payment.id),
            "provider": payment.provider,
            "provider_order_id": payment.provider_order_id,
            "amount_inr": payment.amount_inr,
            "status": payment.status,
            # Mock gateway: the client "confirms" immediately; real gateways redirect.
            "confirm_url": f"/api/v1/payments/{payment.id}/confirm",
        })


class ConfirmView(APIView):
    """POST — mock-gateway confirmation (dev/demo). Real gateways use webhooks."""

    permission_classes = [IsAuthenticatedActive]

    def post(self, request, payment_id):
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        if payment.provider != "mock":
            raise AppError(
                "This payment must be confirmed by the gateway webhook.",
                code="invalid_confirmation_path",
            )
        if payment.order.status == "CANCELLED":
            raise AppError("That order was cancelled.", code="order_cancelled")
        PaymentService.confirm(payment)
        return Response({"status": payment.status,
                         "order_status": payment.order.status})


class WebhookView(APIView):
    """POST /api/v1/payments/webhook/<provider> — AllowAny; signature verified inside."""

    permission_classes = []

    def post(self, request, provider: str):
        payload = request.data or {}
        event_id = str(payload.get("event_id") or request.headers.get("X-Event-Id", ""))
        if not event_id:
            raise AppError("Missing event id.", code="missing_event_id")
        result = PaymentService.handle_webhook(
            provider,
            event_id=event_id,
            event_type=str(payload.get("event_type", "")),
            payload={**payload, "body_sha256": request.headers.get("X-Body-SHA256", "")},
        )
        return Response(result)
