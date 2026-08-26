"""Wardrobe domain services. Views stay thin; logic lives here."""
from django.utils import timezone

from ai import orchestrator
from ai.providers.closet import pick_combination
from analytics.services import record_event
from core.exceptions import AppError
from fashion.registry import OCCASIONS, get_occasion
from wardrobe.models import WardrobeItem
from wardrobe.weather import get_weather

# Keyword → category inference over AI-extracted garment text.
_CATEGORY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("kurta-set", "saree", "lehenga", "sherwani", "anarkali", "salwar", "kurta", "kurti", "dhoti"),
     WardrobeItem.Category.ETHNIC),
    (("dress", "gown", "frock", "jumpsuit"), WardrobeItem.Category.DRESSES),
    (("t-shirt", "tshirt", "shirt", "top", "blouse", "sweater", "hoodie", "tee", "tank", "polo"),
     WardrobeItem.Category.TOPS),
    (("jeans", "trouser", "pant", "chino", "short", "skirt", "jogger", "legging"),
     WardrobeItem.Category.BOTTOMS),
    (("jacket", "blazer", "coat", "shawl", "cape", "cardigan", "parka"),
     WardrobeItem.Category.OUTERWEAR),
    (("shoe", "sneaker", "heel", "flat", "mojari", "sandal", "boot", "loafer", "derby", "slipper"),
     WardrobeItem.Category.FOOTWEAR),
    (("watch", "bag", "belt", "scarf", "jewellery", "jewelry", "earring", "necklace",
      "dupatta", "cap", "hat", "sunglasses", "bracelet", "bangle"),
     WardrobeItem.Category.ACCESSORIES),
]


def guess_category(texts: list[str], fallback: str = "") -> str:
    blob = " ".join(t.lower() for t in texts if t)
    for keywords, category in _CATEGORY_KEYWORDS:
        if any(k in blob for k in keywords):
            return category
    return fallback or WardrobeItem.Category.OTHER


def _item_summary(item: WardrobeItem) -> dict:
    return {
        "id": str(item.id),
        "category": item.category,
        "name": item.name,
        "color_primary": item.color_primary,
        "color_hex": item.color_hex,
        "fabric": item.fabric,
        "pattern": item.pattern,
        "formality": item.formality,
        "occasion_slugs": item.occasion_slugs,
        "favorite": item.favorite,
        "times_worn": item.times_worn,
    }


class WardrobeService:
    @staticmethod
    def ready_items(user) -> list[WardrobeItem]:
        return list(
            WardrobeItem.objects.filter(user=user, archived=False, status=WardrobeItem.Status.READY)
        )

    @staticmethod
    def add_item(user, *, image_bytes: bytes | None = None, filename: str = "item.jpg",
                 category: str = "", notes: str = "") -> WardrobeItem:
        from subscriptions.services import assert_within_quota, get_entitlements

        ent = get_entitlements(user)
        used = WardrobeItem.objects.filter(user=user, archived=False).count()
        try:
            assert_within_quota(ent, "wardrobe_items", used)
        except Exception as exc:
            raise AppError(
                f"You've reached your wardrobe limit of {ent.wardrobe_item_limit} items. "
                "Upgrade your plan or archive old pieces.",
                code="quota_exceeded",
            ) from exc

        item = WardrobeItem.objects.create(
            user=user,
            category=category or WardrobeItem.Category.OTHER,
            notes=(notes or "")[:300],
        )
        if image_bytes:
            item.image.save(f"wardrobe/{item.id}{_ext_for(filename)}", _content_file(image_bytes))

        analysis = orchestrator.extract_wardrobe_attributes(
            user=user, image_bytes=image_bytes or b""
        )
        _apply_analysis(item, analysis)

        if not item.name:
            default = dict(WardrobeItem.Category.choices).get(item.category, "New piece")
            item.name = (notes.strip() or f"{default.title()} · {_colorish(item)}")[:120]
        item.status = WardrobeItem.Status.READY
        item.save()

        record_event(user=user, name="wardrobe_item_added",
                     properties={"item_id": str(item.id), "category": item.category})
        from fashionxp.services import award

        award(user, "item_added", ref_type="item", ref_id=str(item.id))
        return item

    @staticmethod
    def mark_worn(item: WardrobeItem) -> WardrobeItem:
        item.times_worn += 1
        item.last_worn_at = timezone.now()
        item.save(update_fields=["times_worn", "last_worn_at", "updated_at"])
        record_event(user=item.user, name="wardrobe_item_worn",
                     properties={"item_id": str(item.id), "times_worn": item.times_worn})
        return item

    @staticmethod
    def recommend_from_closet(user, *, occasion: str | None = None,
                              budget_inr: int | None = None) -> tuple:
        """AI closet styling → persisted GeneratedOutfit + the items used."""
        from fashion.models import GeneratedOutfit

        items = WardrobeService.ready_items(user)
        if len(items) < 2:
            raise AppError(
                "Add at least 2 wardrobe items first — then we can style your closet.",
                code="wardrobe_too_small",
            )

        orchestrator.enforce_quota(user=user, scope="ai_text")
        summaries = [_item_summary(i) for i in items]
        result = orchestrator.recommend_from_wardrobe(
            user=user, occasion=occasion, budget_inr=budget_inr,
            wardrobe_summary=summaries,
            style_context=_style_context(user),
        )

        valid_ids = {s["id"] for s in summaries}
        used_ids = [i for i in result.used_item_ids if i in valid_ids]

        outfit = GeneratedOutfit.objects.create(
            user=user,
            source=GeneratedOutfit.Source.WARDROBE,
            status=GeneratedOutfit.Status.COMPLETED,
            title=result.headline[:140],
            occasion=occasion or "",
            budget_inr=budget_inr,
            recommendation=result.model_dump(),
            design_state={"wardrobe_item_ids": used_ids},
        )
        record_event(user=user, name="wardrobe_recommendation_completed",
                     properties={"outfit_id": str(outfit.id), "occasion": occasion or "",
                                 "items_used": len(used_ids)})
        return outfit, [i for i in items if str(i.id) in used_ids]

    # ---- Daily assistant (free deterministic path; no AI spend) -------------

    @staticmethod
    def build_daily_suggestion(user, *, city_override: str = "") -> dict:
        profile = getattr(user, "profile", None)
        city = (city_override or getattr(profile, "city", "") or "").strip()
        weather = get_weather(city)

        common: list[str] = []
        sp = getattr(user, "style_profile", None)
        if sp:
            common = list(sp.common_occasions or [])
        weekday = timezone.localdate().weekday()
        work_first = ["office", "business-meeting", "college", "interview"]
        weekend_first = ["party", "date", "dinner", "casual", "festival", "travel"]
        priority = work_first + weekend_first if weekday < 5 else weekend_first + work_first
        occasion = next((o for o in priority if o in common), "casual")

        tips = _weather_tips(weather)
        headline = _daily_headline(weather, occasion)

        closet_payload = None
        items = WardrobeService.ready_items(user)
        if len(items) >= 2:
            summaries = [_item_summary(i) for i in items]
            _, result = pick_combination(summaries, occasion=occasion,
                                         seed=timezone.localdate().isoformat())
            used_ids = set(result.used_item_ids) or set(summaries[i]["id"] for i in range(min(2, len(summaries))))
            used = [i for i in items if str(i.id) in used_ids]
            if used:
                closet_payload = {
                    "recommendation": result.model_dump(),
                    "items": [_brief(i) for i in used],
                }

        record_event(user=user, name="daily_suggestion_viewed",
                     properties={"occasion": occasion, "has_weather": bool(weather)})
        return {
            "date": timezone.localdate().isoformat(),
            "city": weather.city if weather else "",
            "weather": _weather_payload(weather),
            "occasion": occasion,
            "headline": headline,
            "tips": tips,
            "closet_outfit": closet_payload,
        }


# ---- helpers -----------------------------------------------------------------


def _ext_for(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".jpg"
    return ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"


def _content_file(data: bytes):
    from django.core.files.base import ContentFile

    return ContentFile(data)


def _colorish(item: WardrobeItem) -> str:
    return item.color_primary.replace("-", " ").title() if item.color_primary else "Piece"


def _apply_analysis(item: WardrobeItem, analysis) -> None:
    detected = analysis.detected_clothing[0] if analysis.detected_clothing else None
    texts = [detected.category, detected.description] if detected else []
    user_category = "" if item.category == WardrobeItem.Category.OTHER else item.category
    guessed = guess_category(texts, fallback="")
    item.category = user_category or guessed or WardrobeItem.Category.OTHER
    if detected:
        item.pattern = (detected.pattern or "")[:60]
        if detected.fabric:
            item.fabric = detected.fabric[:60]
    if analysis.dominant_colors:
        primary = analysis.dominant_colors[0]
        item.color_primary = primary.name[:40]
        item.color_hex = primary.hex
    item.formality = max(1, min(5, int(analysis.formality_level)))
    item.occasion_slugs = [o for o in analysis.occasion_compatibility if o in OCCASIONS][:6]
    item.style_tags = analysis.style_tags[:6]
    item.seasons = _seasons_from(detected)
    item.attributes = analysis.model_dump()


def _seasons_from(detected) -> list[str]:
    fabric = (detected.fabric if detected else "").lower()
    seasons: list[str] = []
    if any(f in fabric for f in ("wool", "velvet", "tweed", "flannel")):
        seasons.append("winter")
    if any(f in fabric for f in ("cotton", "linen", "mul", "khadi")):
        seasons.extend(["summer", "monsoon"])
    return seasons or ["all-season"]


def _style_context(user) -> dict:
    sp = getattr(user, "style_profile", None)
    if not sp:
        return {}
    return {
        "preferred_styles": sp.preferred_styles,
        "favorite_colors": sp.favorite_colors,
        "avoided_colors": sp.avoided_colors,
        "fit_preference": sp.fit_preference,
        "traditional_modern_balance": sp.traditional_modern_balance,
        "common_occasions": sp.common_occasions,
    }


def _weather_tips(weather) -> list[str]:
    if weather is None:
        return ["Add your city in Profile for weather-aware picks."]
    tips: list[str] = []
    temp = weather.temp_c
    if temp >= 32:
        tips.append("It's hot — stick to breathable cottons/linen and lighter colors.")
    elif temp < 18:
        tips.append("It's cool out — layer up; a jacket or shawl finishes the look.")
    else:
        tips.append("Pleasant weather — most fabrics work; play with layers and texture.")
    if weather.is_rainy:
        tips.append("Rain likely — avoid suede/leather and pick dark soles.")
    return tips


def _daily_headline(weather, occasion: str) -> str:
    label = get_occasion(occasion)
    occ_label = label.label if label else occasion.replace("-", " ").title()
    suffix = f" — {weather.condition}, {round(weather.temp_c)}°C in {weather.city}" if weather else ""
    return f"Ahead: {occ_label}{suffix}"


def _weather_payload(weather) -> dict | None:
    if weather is None:
        return None
    return {
        "temp_c": round(weather.temp_c, 1),
        "condition": weather.condition,
        "is_mock": weather.is_mock,
        "source": weather.source,
    }


def _brief(item: WardrobeItem) -> dict:
    return {
        "id": str(item.id),
        "name": item.name,
        "category": item.category,
        "color_primary": item.color_primary,
        "color_hex": item.color_hex,
        "image": "",  # filled by views (needs request context for absolute URL)
    }
