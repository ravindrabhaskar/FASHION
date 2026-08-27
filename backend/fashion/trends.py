"""Deterministic fashion trends engine (PRD §43).

Aggregates live activity from the catalog, wardrobe, social posts and quote
requests into a cheap, deterministic "what's trending" snapshot. No AI spend:
pure SQL counts + a small normalization layer, fully refreshable per request.
"""

from collections import Counter

import re

from django.db.models import Count

from marketplace.models import Product
from social.models import Post
from wardrobe.models import WardrobeItem


def trend_snapshot(*, limit: int = 8) -> dict:
    """Compute the trending snapshot used by GET /fashion/trends."""
    products = list(Product.objects.filter(is_active=True)
                    .only("category", "city", "fabric", "colors"))
    # Colors are stored as a JSON list per product.
    color_counter: Counter[str] = Counter()
    fabric_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    for p in products:
        for color in (p.colors or [])[:4]:
            color_counter[str(color).strip().lower()] += 1
        if p.fabric:
            fabric_counter[p.fabric.strip().lower()] += 1
        if p.category:
            category_counter[p.category] += 1

    city_counter: Counter[str] = Counter()
    designer_sales = (
        Product.objects.filter(is_active=True)
        .exclude(city="")
        .values_list("city", flat=True)
    )
    for city in designer_sales:
        city_counter[str(city).strip()[:40]] += 1

    # Semantic demand signals: what users are asking for/buying.
    from orders.models import Order

    ordered_categories = (
        Order.objects.filter(status__in=("PAID", "IN_PRODUCTION", "SHIPPED",
                                         "DELIVERED", "COMPLETED"))
        .filter(product__isnull=False)
        .values("product__category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    for row in ordered_categories:
        if row["product__category"]:
            category_counter[row["product__category"]] += row["count"] * 2

    hashtag_counter: Counter[str] = Counter()
    hashtag_re = re.compile(r"#([\w\u0900-\u097F]+)")
    for post in Post.objects.filter(status=Post.Status.PUBLISHED).only("caption"):
        for tag in hashtag_re.findall(post.caption):
            hashtag_counter[tag.strip().lower()] += 1

    wardrobe_counter = Counter(
        WardrobeItem.objects.filter(archived=False)
        .exclude(category="other")
        .values_list("category", flat=True)
    )
    for cat, count in wardrobe_counter.items():
        category_counter[cat] += min(count, 5)

    def top(counter: Counter[str], n: int, label_for=lambda v, c: v) -> list[dict]:
        return [
            {"value": value, "count": count, "label": label_for(value, count)}
            for value, count in counter.most_common(n) if value
        ]

    return {
        "colors": top(color_counter, limit),
        "fabrics": top(fabric_counter, limit),
        "categories": top(category_counter, limit),
        "hashtags": top(hashtag_counter, limit),
        "cities": top(city_counter, limit),
        "generated_at": _now(),
    }


def _now():
    from django.utils import timezone

    return timezone.now().isoformat()