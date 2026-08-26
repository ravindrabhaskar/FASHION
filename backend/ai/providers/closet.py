"""Deterministic wardrobe combination engine.

Pure functions over plain dicts / pydantic schemas — no Django dependencies.
Used by:
- ``MockAIProvider.recommend_from_wardrobe`` (zero-key dev experience)
- the daily style assistant (free deterministic pick, no AI spend)
Real LLM providers receive the same wardrobe summary and return the same schema.
"""
import hashlib

from ai.schemas import ColorSwatch, GarmentSpec, OutfitComponent, RecommendationResult

# WardrobeItem.Category -> outfit slot vocabulary
CATEGORY_SLOTS = {
    "tops": "top",
    "bottoms": "bottom",
    "dresses": "base",       # one-piece look
    "ethnic": "base",        # kurta-set/saree/lehenga treated as one-piece
    "outerwear": "layer",
    "footwear": "footwear",
    "accessories": "accessory",
    "other": "",
}

BREATHABLE_FABRICS = {"cotton", "mul-cotton", "linen", "cotton-silk", "khadi", "oxford-cotton"}


def _hash_int(*parts) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(digest[:8], 16)


def _target_formality(occasion: str | None) -> int:
    from fashion.registry import get_occasion

    spec = get_occasion(occasion or "")
    return spec.formality if spec else 3


def _occasion_label(occasion: str | None) -> str:
    if not occasion:
        return "Everyday"
    from fashion.registry import get_occasion

    spec = get_occasion(occasion)
    return spec.label.title() if spec else occasion.replace("-", " ").title()


def _score(item: dict, *, target_formality: int, occasion: str | None, seed: str) -> float:
    score = 5 - abs(int(item.get("formality") or 3) - target_formality) * 1.5
    if occasion and occasion in (item.get("occasion_slugs") or []):
        score += 3
    if item.get("favorite"):
        score += 0.5
    score += (_hash_int(seed, item["id"]) % 100) / 100  # stable per-item variety
    return score


def pick_combination(
    items: list[dict],
    *,
    occasion: str | None,
    budget_inr: int | None = None,
    seed: str = "",
) -> tuple[list[str], RecommendationResult]:
    """Pick the best available combination from wardrobe summaries.

    Args:
        items: dicts with id/name/category/color_primary/color_hex/fabric/formality/
            occasion_slugs/favorite/times_worn. Must be non-empty READY items.
        occasion: registry slug (optional).
        budget_inr: advisory only for closet looks (items are already owned).
        seed: string mixed into the jitter so different requests vary stably.

    Returns:
        (used_item_ids, RecommendationResult)
    """
    target = _target_formality(occasion)
    scored = sorted(
        items,
        key=lambda it: _score(it, target_formality=target, occasion=occasion, seed=seed),
        reverse=True,
    )

    by_slot: dict[str, list[dict]] = {}
    for item in scored:
        slot = CATEGORY_SLOTS.get(item.get("category") or "other", "")
        if not slot:
            continue
        by_slot.setdefault(slot, []).append(item)

    used_ids: list[str] = []
    chosen: list[tuple[str, dict]] = []  # (outfit_slot, item)

    def take(pool_key: str, outfit_slot: str) -> None:
        for candidate in by_slot.get(pool_key) or []:
            if candidate["id"] not in used_ids:
                used_ids.append(candidate["id"])
                chosen.append((outfit_slot, candidate))
                return

    # Base layer: prefer a one-piece on formal occasions (or when no separates); else top+bottom.
    has_separates = bool(by_slot.get("top")) and bool(by_slot.get("bottom"))
    if target >= 4 or not has_separates:
        take("base", "look")
    if not any(slot == "look" for slot, _ in chosen):
        take("top", "top")
        take("bottom", "bottom")
    if not chosen:
        take("base", "look")

    take("layer", "outerwear")
    take("footwear", "footwear")
    take("accessory", "accessory_1")
    take("accessory", "accessory_2")

    components: list[OutfitComponent] = []
    palette_items: list[dict] = []
    for outfit_slot, it in chosen:
        color = it.get("color_primary") or "neutral"
        components.append(OutfitComponent(
            slot=outfit_slot,
            item=GarmentSpec(
                category=it.get("category", "piece"),
                description=it.get("name") or f"{it.get('category', 'piece')}",
                color=color,
                fabric=it.get("fabric") or "",
                pattern=it.get("pattern") or "",
                details=[f"from your wardrobe · worn {it.get('times_worn', 0)}×"],
            ),
        ))
        if it.get("color_hex", "").startswith("#") and len(it["color_hex"]) == 7:
            palette_items.append(it)

    palette: list[ColorSwatch] = []
    roles = iter(["primary", "secondary", "accent", "neutral"])
    seen_hexes: set[str] = set()
    for it in palette_items[:4]:
        if it["color_hex"] in seen_hexes:
            continue
        seen_hexes.add(it["color_hex"])
        palette.append(ColorSwatch(
            name=it.get("color_primary") or "shade", hex=it["color_hex"], role=next(roles),
        ))

    label = _occasion_label(occasion)
    missing = [name for name, key in (("a top", "top"), ("a bottom", "bottom"),
                                      ("footwear", "footwear")) if not by_slot.get(key)]
    headline = f"{label} look, straight from your closet"
    explanation = (
        f"Assembled from {len(used_ids)} of your own pieces for a {label.lower()} setting."
    )
    tips: list[str] = []
    if missing:
        explanation += f" Adding {', '.join(missing)} would unlock more combinations."
        tips.append(f"Wishlist idea: {', '.join(missing)} in a neutral shade.")
    if budget_inr:
        explanation += f" You asked about ₹{budget_inr} — everything here is already yours."
    breathable = [c for c in components if c.item.fabric in BREATHABLE_FABRICS]
    if breathable:
        tips.append("Breathable fabrics in this look keep it comfortable through long days.")

    return used_ids, RecommendationResult(
        headline=headline,
        explanation=explanation,
        occasion_fit_notes=f"Pieces chosen to match {label.lower()} formality.",
        palette=palette,
        outfit_components=components,
        accessories=[c.item.description for c in components if c.slot.startswith("accessory")],
        footwear_note=next((c.item.description for c in components if c.slot == "footwear"), ""),
        styling_tips=tips[:3],
        confidence=0.75,
        alternatives=["Swap the top/bottom pairing for a monochrome variant"],
        used_item_ids=used_ids,
    )
