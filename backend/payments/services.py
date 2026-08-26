"""Payments service: provider abstraction (mock + Razorpay-ready), idempotent webhooks."""
import hashlib
import hmac
import logging

from django.conf import settings
from django.utils import timezone

from core.exceptions import AppError
from orders.models import Order
from orders.services import OrderService
from payments.models import Payment, WebhookEvent

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def initiate(user, order: Order, *, provider: str = "",
                 idempotency_key: str = "") -> Payment:
        if order.customer_id != user.id:
            raise AppError("Not your order.", code="permission_denied")
        provider = provider or getattr(settings, "PAYMENT_PROVIDER", "mock")
        key = idempotency_key or _default_key(user.id, str(order.id))
        existing = Payment.objects.filter(idempotency_key=key).first()
        if existing:
            return existing  # idempotent retry — never double-charge

        payment = Payment.objects.create(
            order=order, user=user, provider=provider,
            amount_inr=order.amount_inr, idempotency_key=key[:64],
        )
        try:
            if provider == "razorpay":
                _razorpay_create(payment)
            else:
                payment.provider_order_id = f"mock_order_{payment.id.hex[:18]}"
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001 - gateway failures are expected
            payment.status = Payment.Status.FAILED
            payment.error = str(exc)[:255]
            payment.save(update_fields=["status", "error", "updated_at"])
            raise AppError("Payment gateway is unavailable right now.",
                           code="gateway_unavailable") from exc
        payment.save(update_fields=["provider_order_id", "updated_at"])

        if order.status == Order.Status.CREATED:
            OrderService.transition(order, to_status=Order.Status.AWAITING_PAYMENT,
                                    actor=user, note="Payment initiated")
        return payment

    @staticmethod
    def confirm(payment: Payment, *, provider_payment_id: str = "") -> Payment:
        """Mark captured and move the order to PAID (mock path / verified webhook)."""
        if payment.status == Payment.Status.CAPTURED:
            return payment  # idempotent
        payment.provider_payment_id = provider_payment_id or f"mock_pay_{payment.id.hex[:18]}"
        payment.status = Payment.Status.CAPTURED
        payment.save(update_fields=["provider_payment_id", "status", "updated_at"])
        OrderService.transition(
            payment.order, to_status=Order.Status.PAID, actor=None, note="Captured"
        )
        return payment

    @staticmethod
    def handle_webhook(provider: str, *, event_id: str, event_type: str,
                       payload: dict) -> dict:
        """Idempotent webhook processing. Returns {"ok": bool, "note": str}."""
        event, created = WebhookEvent.objects.get_or_create(
            provider=provider, event_id=event_id[:128],
            defaults={"payload": payload, "event_type": event_type[:80]},
        )
        if not created and event.processed_at is not None:
            return {"ok": True, "note": "duplicate_ignored"}
        try:
            note = ""
            if provider == "razorpay":
                _verify_razorpay_signature(payload)
            payment = None
            if event_type in ("payment.captured", "mock.payment_captured"):
                reference = str(payload.get("provider_order_id") or "")
                payment = Payment.objects.filter(
                    provider_order_id=reference, provider=provider
                ).first() or Payment.objects.filter(
                    idempotency_key=str(payload.get("idempotency_key") or "")
                ).first()
                if not payment:
                    note = "unknown_reference"
                elif payment.status != Payment.Status.CAPTURED:
                    PaymentService.confirm(
                        payment,
                        provider_payment_id=str(payload.get("provider_payment_id", "")),
                    )
                    note = "captured"
            ok = note != "unknown_reference"
        except Exception as exc:  # noqa: BLE001 - store the failure, don't crash
            event.note = str(exc)[:255]
            event.save(update_fields=["note"])
            raise
        event.processed_at = timezone.now()
        event.ok = ok
        event.note = note[:255]
        event.save(update_fields=["processed_at", "ok", "note"])
        return {"ok": ok, "note": note or "ignored"}


def _default_key(user_id, order_id: str) -> str:
    digest = hashlib.sha256(f"{user_id}|{order_id}|payments.v1".encode()).hexdigest()
    return digest


def _razorpay_create(payment: Payment) -> None:
    base_url = getattr(settings, "RAZORPAY_BASE_URL", "https://api.razorpay.com/v1")
    key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not (key_id and key_secret):
        raise AppError("Razorpay credentials aren't configured.", code="gateway_not_configured")
    import base64

    import httpx

    auth = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    response = httpx.post(
        f"{base_url}/orders",
        headers={"Authorization": f"Basic {auth}"},
        json={
            "amount": payment.amount_inr * 100,  # paise
            "currency": payment.currency,
            "receipt": payment.idempotency_key[:40],
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"razorpay {response.status_code}: {response.text[:120]}")
    payment.provider_order_id = response.json().get("id", "")


def _verify_razorpay_signature(payload: dict) -> None:
    secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")
    received = str(payload.get("signature", ""))
    body_digest = str(payload.get("body_sha256", ""))
    if not secret:
        logger.warning("RAZORPAY_WEBHOOK_SECRET unset; signature check skipped")
        return
    expected = hmac.new(secret.encode(), body_digest.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise AppError("Invalid webhook signature.", code="invalid_webhook_signature")
