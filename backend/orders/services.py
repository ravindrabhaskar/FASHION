"""Order domain service: creation from quotes/catalog + guarded state transitions."""
from analytics.services import record_event
from core.exceptions import AppError
from core.services import get_config
from marketplace.models import QuoteOffer
from orders.models import Order, OrderEvent

# Allowed transitions of the order state machine (PRD §30).
TRANSITIONS: dict[str, set[str]] = {
    Order.Status.CREATED: {Order.Status.AWAITING_PAYMENT, Order.Status.CANCELLED},
    Order.Status.AWAITING_PAYMENT: {Order.Status.PAID, Order.Status.CANCELLED},
    Order.Status.PAID: {Order.Status.IN_PRODUCTION, Order.Status.SHIPPED,
                        Order.Status.REFUNDED, Order.Status.CANCELLED},
    Order.Status.IN_PRODUCTION: {Order.Status.SHIPPED, Order.Status.CANCELLED},
    Order.Status.SHIPPED: {Order.Status.DELIVERED, Order.Status.REFUNDED},
    Order.Status.DELIVERED: {Order.Status.COMPLETED, Order.Status.REFUNDED},
    Order.Status.COMPLETED: set(),
    Order.Status.CANCELLED: set(),
    Order.Status.REFUNDED: set(),
}

CUSTOMER_ALLOWED = {
    Order.Status.CREATED: {Order.Status.AWAITING_PAYMENT, Order.Status.CANCELLED},
    Order.Status.AWAITING_PAYMENT: {Order.Status.PAID, Order.Status.CANCELLED},
    Order.Status.DELIVERED: {Order.Status.COMPLETED},
}


def order_payload(order: Order) -> dict:
    return {
        "id": str(order.id),
        "title": order.title_snapshot,
        "status": order.status,
        "quantity": order.quantity,
        "amount_inr": order.amount_inr,
        "variant_snapshot": order.variant_snapshot,
        "product_id": str(order.product_id) if order.product_id else None,
        "seller_user_id": str(order.seller_user_id),
        "seller_name": order.seller_user.full_name if order.seller_user_id else "",
        "customer_name": order.customer.full_name if order.customer_id else "",
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "created_at": order.created_at,
    }


class OrderService:
    @staticmethod
    def create_from_offer(user, offer: QuoteOffer) -> Order:
        quote_request = offer.request
        designer = quote_request.designer
        commission_pct = float(get_config("marketplace.commission_percent", 12) or 12)
        order = Order.objects.create(
            customer=user,
            seller_user=designer.user if designer else user,
            designer=designer,
            quote_request=quote_request,
            title_snapshot=f"Custom: {quote_request.brief[:120]}",
            amount_inr=offer.price_inr,
            commission_inr=int(offer.price_inr * commission_pct / 100),
            status=Order.Status.CREATED,
            notes=quote_request.brief[:500],
        )
        _log_event(order, to_status=Order.Status.CREATED, created_by=user,
                   note=f"From offer ₹{offer.price_inr}")
        record_event(user=user, name="order_created",
                     properties={"order_id": str(order.id), "amount_inr": order.amount_inr})
        return order

    @staticmethod
    def create_from_catalog(user, product, *, quantity: int = 1) -> Order:
        """Buy a ready-to-ship product directly from the catalog."""
        from core.services import get_config

        if not getattr(product, "is_active", True):
            raise AppError("That product isn't available.", code="product_inactive")
        if product.stock < quantity:
            raise AppError("Not enough stock.", code="insufficient_stock")
        quantity = max(1, min(int(quantity), product.stock))
        commission_pct = float(get_config("marketplace.commission_percent", 12) or 12)
        amount = product.price_inr * quantity
        order = Order.objects.create(
            customer=user,
            seller_user=product.seller_user,
            designer=product.designer,
            brand=product.brand,
            product=product,
            title_snapshot=product.title[:160],
            quantity=quantity,
            amount_inr=amount,
            commission_inr=int(amount * commission_pct / 100),
            status=Order.Status.CREATED,
        )
        _log_event(order, to_status=Order.Status.CREATED, created_by=user,
                   note="From catalog purchase")
        record_event(user=user, name="order_created",
                     properties={"order_id": str(order.id), "amount_inr": amount})
        from notifications.services import notify

        notify(user, type="order", title="Order created 🧾",
               body=product.title[:100], data={"order_id": str(order.id)})
        return order

    @staticmethod
    def transition(order: Order, *, to_status: str, actor=None,
                   note: str = "") -> Order:
        if to_status not in dict(Order.Status.choices):
            raise AppError("Unknown order status.", code="invalid_status")
        allowed = TRANSITIONS.get(order.status, set())
        if to_status not in allowed:
            raise AppError(
                f"Can't move an order from {order.status} to {to_status}.",
                code="invalid_transition",
            )
        if actor is not None and getattr(actor, "id", None) == order.customer_id:
            if to_status not in CUSTOMER_ALLOWED.get(order.status, set()):
                raise AppError("Only the seller can do that.", code="permission_denied")
        elif actor is not None and getattr(actor, "id", None) != order.seller_user_id \
                and not getattr(actor, "is_superuser", False):
            raise AppError("Not your order.", code="permission_denied")

        previous = order.status
        order.status = to_status
        order.save(update_fields=["status", "updated_at"])
        _log_event(order, from_status=previous, to_status=to_status, created_by=actor, note=note)

        event_name = {
            Order.Status.PAID: "order_paid",
            Order.Status.SHIPPED: "order_shipped",
            Order.Status.DELIVERED: "order_delivered",
            Order.Status.COMPLETED: "order_completed",
            Order.Status.CANCELLED: "order_cancelled",
            Order.Status.REFUNDED: "order_refunded",
        }.get(to_status, "order_updated")
        record_event(user=order.customer, name=event_name,
                     properties={"order_id": str(order.id)})
        from notifications.services import notify

        notify(order.customer, type="order", title=f"Order {to_status.lower().replace('_', ' ')}",
               body=order.title_snapshot[:100], data={"order_id": str(order.id)})
        return order


def _log_event(order: Order, *, from_status: str = "", to_status: str,
               created_by=None, note: str = "") -> None:
    OrderEvent.objects.create(
        order=order, from_status=from_status or "", to_status=to_status,
        note=note[:255], created_by=created_by if getattr(created_by, "is_authenticated", False) else None,
    )
