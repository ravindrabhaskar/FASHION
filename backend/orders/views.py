"""Orders API: list, detail, seller/customer transitions."""
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from orders.models import Order
from orders.services import OrderService, order_payload


class OrderListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        scope = request.query_params.get("scope", "mine")
        qs = (Order.objects.filter(customer=request.user) if scope == "mine"
              else Order.objects.filter(seller_user=request.user))
        rows = qs[:50]
        return Response({"count": len(rows), "results": [order_payload(o) for o in rows]})


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, order_id):
        order = _visible_order(request, order_id)
        payload = order_payload(order)
        payload["events"] = [
            {"from_status": e.from_status, "to_status": e.to_status,
             "note": e.note, "created_at": e.created_at}
            for e in order.events.all()
        ]
        return Response(payload)


class OrderTransitionView(APIView):
    """POST {status, note?} — state machine transition by the allowed party."""

    permission_classes = [IsAuthenticatedActive]

    def post(self, request, order_id):
        order = _visible_order(request, order_id)
        payload = request.data or {}
        updated = OrderService.transition(
            order,
            to_status=str(payload.get("status", "")),
            actor=request.user,
            note=str(payload.get("note", "")),
        )
        return Response(order_payload(updated))


def _visible_order(request, order_id) -> Order:
    order = get_object_or_404(Order, id=order_id)
    involved = (order.customer_id == request.user.id
                or order.seller_user_id == request.user.id
                or request.user.is_superuser)
    if not involved:
        raise AppError("Not your order.", code="permission_denied")
    return order
