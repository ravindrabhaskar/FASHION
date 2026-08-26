"""Marketplace API: catalog, search, shop-this-look, customize quotes."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from core.exceptions import AppError
from marketplace.models import Product, QuoteOffer, QuoteRequest
from marketplace.services import (
    CatalogService,
    QuoteService,
    product_payload,
)
from wardrobe.views import _validate_image_upload


class ProductsView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        products = Product.objects.filter(is_active=True).prefetch_related("variants", "images")
        for field in ("category", "city"):
            value = request.query_params.get(field, "")
            if value:
                products = products.filter(**{f"{field}__iexact": value})
        mine = request.query_params.get("mine") == "true"
        if mine:
            products = products.filter(seller_user=request.user)
        limit = min(int(request.query_params.get("limit", "24") or 24), 60)
        return Response({
            "count": products.count(),
            "results": [product_payload(p) for p in products[:limit]],
        })

    def post(self, request):
        payload = request.data or {} if not request.FILES else {**request.data}
        photo = request.FILES.get("photo")
        product = CatalogService.create_product(user=request.user, payload=payload)
        if photo:
            from marketplace.models import ProductImage

            image_bytes = _validate_image_upload(photo)
            from wardrobe.services import _content_file, _ext_for

            img = ProductImage(product=product, alt=product.title[:160])
            img.image.save(f"products/{product.id}{_ext_for(getattr(photo, 'name', 'x.jpg'))}",
                           _content_file(image_bytes))
            img.save()
        return Response(product_payload(product), status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, product_id):
        product = get_object_or_404(
            Product, id=product_id, is_active=True
        )
        return Response(product_payload(product))

    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, seller_user=request.user)
        payload = request.data or {}
        for field in ("title", "description", "fabric"):
            if field in payload:
                setattr(product, field, str(payload[field])[:4000])
        for field in ("price_inr", "stock"):
            if field in payload:
                try:
                    setattr(product, field, max(1 if field == "price_inr" else 0, int(payload[field])))
                except (TypeError, ValueError) as exc:
                    raise AppError(f"Invalid {field}.", code="validation_error") from exc
        for field in ("is_customizable", "ready_to_ship", "is_active"):
            if field in payload:
                setattr(product, field, bool(payload[field]))
        product.save()
        return Response(product_payload(product))

    def delete(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, seller_user=request.user)
        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchView(APIView):
    """POST {query, category?, city?, max_price?} — semantic fashion search."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        payload = request.data or {}
        results = CatalogService.search(
            request.user,
            query=str(payload.get("query", ""))[:200],
            category=str(payload.get("category", "")),
            city=str(payload.get("city", "")),
            max_price=payload.get("max_price"),
        )
        record_event(user=request.user, name="product_searched",
                     properties={"query": str(payload.get("query", ""))[:100],
                                 "results": len(results)})
        return Response({"count": len(results), "results": results})


class ShopThisLookView(APIView):
    """GET — resolve a post's tagged components into shoppable products/items."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request, post_id):
        from social.models import Post

        post = get_object_or_404(Post, id=post_id)
        components = []
        for tag in post.item_tags.all():
            entry = {
                "id": str(tag.id), "label": tag.label, "position": tag.position,
                "product": None,
            }
            if tag.product and tag.product.is_active:
                entry["product"] = product_payload(tag.product)
            elif tag.wardrobe_item:
                from wardrobe.models import WardrobeItem

                item = WardrobeItem.objects.filter(id=tag.wardrobe_item_id).first()
                similar: list[Product] = []
                if item and item.category != "other":
                    similar = list(Product.objects.filter(
                        is_active=True, category=item.category,
                    ).order_by("-created_at")[:3])
                entry["similar_products"] = [product_payload(p) for p in similar]
            components.append(entry)
        return Response({"post_id": str(post.id), "components": components})


# ---- Customize quotes ----------------------------------------------------------


class QuoteRequestView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        scope = request.query_params.get("scope", "mine")
        qs = QuoteRequest.objects.select_related("designer", "product")
        if scope == "incoming":
            profile = getattr(request.user, "designer_profile", None)
            if not profile:
                raise AppError("You don't have a designer profile.", code="no_designer_profile")
            qs = qs.filter(designer=profile)
        else:
            qs = qs.filter(customer=request.user)
        rows = qs[:50]
        return Response({
            "results": [_request_payload(r) for r in rows],
        })

    def post(self, request):
        payload = request.data or {}
        designer = None
        if payload.get("designer_slug"):
            from designers.models import DesignerProfile

            designer = DesignerProfile.objects.filter(slug=payload["designer_slug"]).first()
        product = None
        if payload.get("product_id"):
            product = Product.objects.filter(id=payload["product_id"], is_active=True).first()
        design_ref = None
        if payload.get("outfit_id"):
            from fashion.models import GeneratedOutfit

            design_ref = GeneratedOutfit.objects.filter(
                id=payload["outfit_id"], user=request.user
            ).first()

        budget_raw = payload.get("budget_inr")
        try:
            budget_inr = int(budget_raw) if budget_raw else None
        except (TypeError, ValueError) as exc:
            raise AppError("Budget must be rupees.", code="invalid_budget") from exc

        quote_request = QuoteService.create_request(
            request.user,
            brief=str(payload.get("brief", "")),
            budget_inr=budget_inr,
            designer=designer,
            product=product,
            design_ref=design_ref,
        )
        return Response(_request_payload(quote_request), status=status.HTTP_201_CREATED)


class QuoteOfferView(APIView):
    """GET offers on a request · POST a new offer (designer only)."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request, request_id):
        quote_request = _own_or_targetted(request, request_id)
        return Response({"results": [
            {
                "id": str(o.id), "price_inr": o.price_inr, "timeline_days": o.timeline_days,
                "notes": o.notes, "status": o.status, "created_at": o.created_at,
            }
            for o in quote_request.offers.all()
        ]})

    def post(self, request, request_id):
        quote_request = get_object_or_404(QuoteRequest, id=request_id)
        payload = request.data or {}
        offer = QuoteService.offer(
            request.user, quote_request,
            price_inr=payload.get("price_inr"),
            timeline_days=payload.get("timeline_days") or 14,
            notes=str(payload.get("notes", "")),
        )
        return Response({
            "id": str(offer.id), "price_inr": offer.price_inr,
            "timeline_days": offer.timeline_days, "status": offer.status,
        }, status=status.HTTP_201_CREATED)


class QuoteAcceptView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, offer_id):
        offer = get_object_or_404(QuoteOffer, id=offer_id)
        order = QuoteService.accept(request.user, offer)
        from orders.services import order_payload

        return Response(order_payload(order), status=status.HTTP_201_CREATED)


def _own_or_targetted(request, request_id) -> QuoteRequest:
    quote_request = get_object_or_404(QuoteRequest, id=request_id)
    is_customer = quote_request.customer_id == request.user.id
    is_designer = (quote_request.designer is not None
                   and quote_request.designer.user_id == request.user.id)
    if not (is_customer or is_designer or request.user.is_superuser):
        raise AppError("This conversation isn't yours.", code="permission_denied")
    return quote_request


def _request_payload(r: QuoteRequest) -> dict:
    latest_offer = r.offers.order_by("-created_at").first()
    return {
        "id": str(r.id),
        "brief": r.brief[:280],
        "budget_inr": r.budget_inr,
        "status": r.status,
        "designer": {"slug": r.designer.slug, "studio_name": r.designer.studio_name}
        if r.designer else None,
        "product_title": r.product.title if r.product else "",
        "offers": [
            {
                "id": str(o.id), "price_inr": o.price_inr, "timeline_days": o.timeline_days,
                "notes": o.notes, "status": o.status,
            }
            for o in ([latest_offer] if latest_offer else [])
        ],
        "created_at": r.created_at,
    }
