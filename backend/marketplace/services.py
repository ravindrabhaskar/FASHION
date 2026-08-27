"""Marketplace services: product catalog + semantic search + quote lifecycle."""
from django.utils import timezone

from analytics.services import record_event
from core.exceptions import AppError
from core.services import get_config
from marketplace.models import Product, ProductVariant, QuoteOffer, QuoteRequest


class CatalogService:
    @staticmethod
    def create_product(user, *, payload: dict) -> Product:
        designer = getattr(user, "designer_profile", None)
        brand = getattr(user, "brand_profile", None)
        if not designer and not brand:
            raise AppError(
                "Only designer or brand accounts can list products.", code="seller_required"
            )
        title = str(payload.get("title", "")).strip()
        price_raw = payload.get("price_inr")
        try:
            price_inr = max(1, int(price_raw))
        except (TypeError, ValueError) as exc:
            raise AppError("Price must be rupees.", code="invalid_price") from exc
        if not title or price_inr <= 0:
            raise AppError("Title and a valid price are required.", code="validation_error")

        product = Product.objects.create(
            seller_user=user,
            designer=designer,
            brand=brand,
            title=title[:160],
            description=str(payload.get("description", ""))[:4000],
            category=str(payload.get("category", Product.Category.WESTERN)),
            price_inr=price_inr,
            city=str(payload.get("city", "") or (designer.city if designer else ""))[:80],
            fabric=str(payload.get("fabric", ""))[:60],
            colors=[str(c).lower() for c in (payload.get("colors") or [])][:8],
            tags=[str(t).lower() for t in (payload.get("tags") or [])][:12],
            is_customizable=bool(payload.get("is_customizable")),
            ready_to_ship=bool(payload.get("ready_to_ship", True)),
            stock=max(0, int(payload.get("stock") or 1)),
        )
        for variant in (payload.get("variants") or [])[:10]:
            ProductVariant.objects.create(
                product=product,
                name=str(variant.get("name", "Size"))[:40],
                value=str(variant.get("value", ""))[:60],
                price_delta_inr=int(variant.get("price_delta_inr") or 0),
                stock=max(0, int(variant.get("stock") or 0)),
            )
        record_event(user=user, name="product_listed",
                     properties={"product_id": str(product.id), "category": product.category})
        return product

    @staticmethod
    def ensure_embedding(product: Product) -> None:
        """Best-effort semantic embedding for search; mock provider works offline."""
        from ai import orchestrator

        if product.embedding and product.embedding_model == orchestrator._provider().name:
            return
        text = ". ".join(filter(None, [
            product.title, product.description, product.fabric, product.city,
            " ".join(product.tags), " ".join(product.colors), product.get_category_display(),
        ]))
        vectors = orchestrator.embed([text])
        product.embedding = vectors[0]
        product.embedding_model = orchestrator._provider().name
        product.save(update_fields=["embedding", "embedding_model"])

    @staticmethod
    def search(user, *, query: str, category: str = "", city: str = "",
               max_price=None, limit: int = 20) -> list[dict]:
        products = Product.objects.filter(is_active=True).select_related("designer", "brand")
        if category:
            products = products.filter(category=category)
        if city:
            products = products.filter(city__iexact=city)
        if max_price:
            products = products.filter(price_inr__lte=int(max_price))
        query = query.strip()
        results: list[tuple[float, Product]] = []

        if query:
            from ai import orchestrator

            qvec = orchestrator.embed([query.lower()])[0]
            scored: list[tuple[float, Product]] = []
            for p in products[:500]:
                CatalogService.ensure_embedding(p)
                score = _cosine(qvec, p.embedding) if p.embedding else 0.0
                # lexical boost keeps exact matches competitive with vector similarity
                blob = f"{p.title} {p.description} {p.fabric} {' '.join(p.tags)}".lower()
                if query.lower() in blob:
                    score += 0.5
                if score > 0.05:
                    scored.append((score, p))
            scored.sort(key=lambda pair: -pair[0])
            results = scored
        else:
            results = [(1.0, p) for p in products]

        return [
            {**product_payload(p), "relevance": round(score, 3)}
            for score, p in results[:limit]
        ]


class QuoteService:
    @staticmethod
    def create_request(user, *, brief: str, budget_inr=None, designer=None,
                       product=None, design_ref=None) -> QuoteRequest:
        brief = brief.strip()
        if len(brief) < 20:
            raise AppError(
                "Describe what you'd like customized (at least 20 characters).",
                code="brief_too_short",
            )
        if designer is None and product is None:
            raise AppError("Pick a designer or a product to customize.",
                           code="quote_target_required")
        request = QuoteRequest.objects.create(
            customer=user, designer=designer, product=product, design_ref=design_ref,
            brief=brief[:2000], budget_inr=budget_inr,
        )
        record_event(user=user, name="quote_requested",
                     properties={"request_id": str(request.id)})
        if designer:
            from notifications.services import notify

            notify(designer.user, type="quote", title="New customization request ✂",
                   body=brief[:80], data={"request_id": str(request.id)})
        return request

    @staticmethod
    def offer(user, request_obj: QuoteRequest, *, price_inr: int,
              timeline_days: int, notes: str = "") -> QuoteOffer:
        if request_obj.designer is None or request_obj.designer.user_id != user.id:
            raise AppError("Only the requested designer can respond.", code="not_quote_designer")
        if request_obj.status != QuoteRequest.Status.NEW:
            raise AppError("This request isn't open for offers.", code="quote_not_open")
        QuoteOffer.objects.filter(request=request_obj, status=QuoteOffer.Status.PROPOSED).update(
            status=QuoteOffer.Status.SUPERSEDED
        )
        offer = QuoteOffer.objects.create(
            request=request_obj, price_inr=max(1, int(price_inr)),
            timeline_days=max(1, min(int(timeline_days), 180)),
            notes=notes[:1000], created_by=user,
        )
        request_obj.status = QuoteRequest.Status.RESPONDED
        request_obj.save(update_fields=["status", "updated_at"])
        commission_pct = float(get_config("marketplace.commission_percent", 12) or 12)

        from notifications.services import notify

        notify(request_obj.customer, type="quote", title="Your quote is ready 🧾",
               body=f"₹{offer.price_inr} · {offer.timeline_days} days",
               data={"request_id": str(request_obj.id), "offer_id": str(offer.id)})
        record_event(user=request_obj.customer, name="quote_offered",
                     properties={"request_id": str(request_obj.id),
                                 "commission_percent": commission_pct})
        return offer

    @staticmethod
    def accept(user, offer: QuoteOffer):
        """Customer accepts → order created via orders service."""
        from orders.services import OrderService

        request_obj = offer.request
        if request_obj.customer_id != user.id:
            raise AppError("This quote isn't yours to accept.", code="not_your_quote")
        if offer.status != QuoteOffer.Status.PROPOSED or \
                request_obj.status != QuoteRequest.Status.RESPONDED:
            raise AppError("That offer is no longer available.", code="offer_unavailable")
        order = OrderService.create_from_offer(user, offer)
        offer.status = QuoteOffer.Status.ACCEPTED
        offer.save(update_fields=["status"])
        request_obj.status = QuoteRequest.Status.ACCEPTED
        request_obj.save(update_fields=["status"])
        record_event(user=user, name="quote_accepted",
                     properties={"request_id": str(request_obj.id), "order_id": str(order.id)})
        return order


def product_payload(product: Product) -> dict:
    first_image = product.images.first()
    image_url = ""
    if first_image:
        image_url = (first_image.image.url if hasattr(first_image.image, "url")
                     else str(first_image.image))
        if image_url.startswith("/"):
            from django.conf import settings as dj_settings

            image_url = f"http://localhost:8000{image_url}" if dj_settings.DEBUG else image_url
    return {
        "id": str(product.id),
        "title": product.title,
        "description": product.description[:280],
        "category": product.category,
        "price_inr": product.price_inr,
        "sale_price_inr": product.sale_price_inr,
        "city": product.city,
        "fabric": product.fabric,
        "colors": product.colors,
        "is_customizable": product.is_customizable,
        "ready_to_ship": product.ready_to_ship,
        "in_stock": product.stock > 0 or bool(product.variants.count()),
        "seller_user_id": str(product.seller_user_id),
        "seller_type": ("designer" if product.designer else "brand" if product.brand else ""),
        "seller_name": (product.designer.studio_name if product.designer
                        else product.brand.name if product.brand else ""),
        "image": image_url,
        "variants": [
            {"id": str(v.id), "name": v.name, "value": v.value,
             "price_delta_inr": v.price_delta_inr, "stock": v.stock}
            for v in product.variants.all()
        ],
    }


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
