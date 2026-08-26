"""Deterministic MockProvider — full product experience with zero external calls.

Outputs are high-quality and occasion-aware so dev/demo/test environments show
the real product behavior. Real providers implement the same protocol.
"""
import hashlib

from ai.schemas import (
    BudgetLine,
    ColorSwatch,
    DesignState,
    DesignTurnResponse,
    GarmentSpec,
    ImageAnalysis,
    OutfitComponent,
    RecommendationResult,
)

OCCASION_OUTFITS: dict[str, dict] = {
    "wedding": {
        "headline": "Regal jewel-tone festive set",
        "components": [
            ("top", GarmentSpec(category="kurta", description="Deep emerald silk kurta with gold zari border",
                                color="emerald-green", fabric="raw-silk", pattern="zari-border",
                                details=["mandarin collar", "full sleeves"])),
            ("bottom", GarmentSpec(category="churidar", description="Ivory churidar with subtle sheen",
                                   color="ivory", fabric="cotton-silk")),
            ("outerwear", GarmentSpec(category="dupatta/shawl", description="Gold-tissue dupatta",
                                      color="gold", fabric="tissue")),
            ("footwear", GarmentSpec(category="mojaris", description="Embroidered gold mojaris",
                                     color="gold", fabric="leather")),
        ],
        "palette": [("emerald", "#0B6E4F", "primary"), ("gold", "#D4AF37", "accent"),
                    ("ivory", "#FFFFF0", "neutral"), ("maroon", "#7C1E2E", "secondary")],
        "accessories": ["Kada or sleek bracelet", "Pearl stud earrings / cufflinks", "Small embroidered potli or pocket square"],
        "tips": ["Keep jewellery to one statement piece to let the kurta breathe.",
                 "A light steam press makes raw-silk read far more premium."],
    },
    "office": {
        "headline": "Crisp modern workday layering",
        "components": [
            ("top", GarmentSpec(category="shirt", description="Sky-blue poplin shirt, semi-cutaway collar",
                                color="sky-blue", fabric="poplin-cotton", details=["semi-cutaway collar"])),
            ("bottom", GarmentSpec(category="trousers", description="Charcoal tapered trousers",
                                   color="charcoal", fabric="wool-blend")),
            ("outerwear", GarmentSpec(category="blazer", description="Navy unstructured blazer",
                                      color="navy", fabric="poly-viscose")),
            ("footwear", GarmentSpec(category="derbies", description="Tan leather derbies",
                                     color="tan-brown", fabric="leather")),
        ],
        "palette": [("navy", "#1B2A4A", "primary"), ("charcoal", "#3B3B3B", "secondary"),
                    ("sky-blue", "#9CC3DD", "accent"), ("white", "#FAFAFA", "neutral")],
        "accessories": ["Minimal steel watch", "Slim leather belt matching shoes"],
        "tips": ["Sleeve should end just at the wrist bone for the sharpest line.",
                 "Keep the blazer buttoned while standing, open when seated."],
    },
}

DEFAULT_OUTFIT = {
    "headline": "Effortless smart-casual look",
    "components": [
        ("top", GarmentSpec(category="shirt", description="Off-white oxford shirt",
                            color="off-white", fabric="oxford-cotton")),
        ("bottom", GarmentSpec(category="trousers", description="Olive relaxed chinos",
                               color="olive", fabric="cotton-twill")),
        ("footwear", GarmentSpec(category="sneakers", description="Clean white leather sneakers",
                                 color="white", fabric="leather")),
    ],
    "palette": [("olive", "#6B8E23", "primary"), ("off-white", "#FDFAF6", "neutral"),
                ("tan-brown", "#B5835A", "accent")],
    "accessories": ["Canvas strap watch", "Tortoise-shell sunglasses (daytime)"],
    "tips": ["Front-tuck the shirt for a relaxed but intentional silhouette."],
}


def _hash_int(*parts) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(digest[:8], 16)


class MockAIProvider:
    """Implements the provider protocol deterministically. Provider name: 'mock'."""

    name = "mock"

    # ---- Vision ---------------------------------------------------------
    def analyze_image(self, *, image_bytes: bytes, occasion: str | None = None,
                      user_notes: str = "") -> ImageAnalysis:
        seed = _hash_int(len(image_bytes), occasion or "", user_notes)
        palettes = [
            [ColorSwatch(name="indigo", hex="#283593", role="primary"),
             ColorSwatch(name="white", hex="#FAFAFA", role="neutral"),
             ColorSwatch(name="mustard", hex="#D4A017", role="accent")],
            [ColorSwatch(name="blush-pink", hex="#E8B4BC", role="primary"),
             ColorSwatch(name="cream", hex="#FFF8E7", role="neutral"),
             ColorSwatch(name="dusty-teal", hex="#5F9EA0", role="secondary")],
            [ColorSwatch(name="olive", hex="#708238", role="primary"),
             ColorSwatch(name="beige", hex="#E6DACD", role="neutral"),
             ColorSwatch(name="rust", hex="#B7410E", role="accent")],
        ]
        return ImageAnalysis(
            detected_clothing=[
                GarmentSpec(category="top", description="Printed cotton shirt", color="indigo",
                            fabric="cotton", pattern="floral-print"),
                GarmentSpec(category="bottom", description="Straight-fit jeans", color="denim-blue",
                            fabric="denim"),
            ],
            dominant_colors=palettes[seed % 3],
            style_tags=["smart-casual", "contemporary", "breathable-fabrics"],
            formality_level=(seed % 2) + 2,
            occasion_compatibility=["casual", "college", "travel", "date"] if not occasion else
            ["casual", "college", "travel", occasion],
            summary="Relaxed smart-casual outfit built around breathable fabrics and a versatile palette.",
        )

    # ---- LLM ------------------------------------------------------------
    def recommend(self, *, analysis: ImageAnalysis | None, occasion: str | None,
                  budget_inr: int | None, user_notes: str = "",
                  style_context: dict | None = None,
                  language: str = "en") -> RecommendationResult:
        spec = OCCASION_OUTFITS.get((occasion or "").lower(), DEFAULT_OUTFIT)
        budget_total = budget_inr or 3500
        allocation = [
            BudgetLine(component=spec["components"][0][1].category, amount_inr=int(budget_total * 0.45)),
            BudgetLine(component=spec["components"][1][1].category, amount_inr=int(budget_total * 0.30)),
            BudgetLine(component="Footwear", amount_inr=int(budget_total * 0.25)),
        ]
        return RecommendationResult(
            headline=spec["headline"],
            explanation=(
                f"For a {occasion or 'casual'} setting this look balances comfort and polish. "
                + (f"Your note — \"{user_notes}\" — shaped the palette. " if user_notes else "")
                + (f"It stays within your ₹{budget_inr} budget. " if budget_inr else "")
                + "Swap any single component without breaking the palette."
            ),
            occasion_fit_notes=f"Appropriate for {occasion or 'casual'} settings; formality tuned to context.",
            palette=[ColorSwatch(name=n, hex=h, role=r) for n, h, r in spec["palette"]],
            outfit_components=[OutfitComponent(slot=s, item=g) for s, g in spec["components"]],
            accessories=list(spec["accessories"]),
            footwear_note=next((g.description for s, g in spec["components"] if s == "footwear"),
                              "Clean neutral footwear completes the look."),
            budget_total_inr=budget_total if budget_inr else None,
            budget_allocation=allocation if budget_inr else [],
            styling_tips=list(spec["tips"]),
            confidence=0.82,
            alternatives=[
                "Monochrome variant: same silhouette, single color family",
                "Texture-forward variant: swap prints for textured solids",
            ],
        )

    def design_turn(self, *, message: str, design_state: DesignState | None,
                    language: str = "en") -> DesignTurnResponse:
        state = design_state or DesignState()
        changes: list[str] = []
        lower = message.lower()

        # Each rule is a set of trigger substrings (any one activates it).
        rules = [
            ({"maroon", "red"}, "base_color", "maroon", "base color"),
            ({"emerald", "green"}, "base_color", "emerald-green", "base color"),
            ({"navy", "blue"}, "base_color", "navy", "base color"),
            ({"black"}, "base_color", "black", "base color"),
            ({"pastel"}, "base_color", "pastel-lilac", "base color"),
            ({"white", "ivory"}, "base_color", "ivory", "base color"),
            ({"pink"}, "base_color", "blush-pink", "base color"),
            ({"yellow", "haldi"}, "base_color", "marigold", "base color"),
            ({"gold accent", "golden border"}, None, None, None),  # placeholder no-op
            ({"silver accent"}, "accent_color", "silver", "accent color"),
            ({"lighter fabric", "summer", "hot weather", "hot", "breathable", "mul"},
             "fabric", "mul-cotton", "fabric"),
            ({"silk"}, "fabric", "cotton-silk", "fabric"),
            ({"linen"}, "fabric", "linen", "fabric"),
            ({"sleeveless"}, "sleeve_style", "sleeveless", "sleeves"),
            ({"full sleeve", "long sleeve", "full sleeves"}, "sleeve_style", "full", "sleeves"),
            ({"short sleeve", "short sleeves"}, "sleeve_style", "short", "sleeves"),
            ({"three-quarter", "3/4 sleeve"}, "sleeve_style", "three-quarter", "sleeves"),
            ({"v-neck", "v neck"}, "collar_neckline", "v-neck", "neckline"),
            ({"boat neck", "boatneck"}, "collar_neckline", "boat", "neckline"),
            ({"collar", "mandarin"}, "collar_neckline", "mandarin", "neckline"),
            ({"knee length", "shorter"}, "length", "knee", "length"),
            ({"ankle", "longer"}, "length", "ankle", "length"),
            ({"midi"}, "length", "midi", "length"),
            ({"no embroidery", "remove embroidery"}, "embroidery_level", "none", "embroidery"),
            ({"heavy embroidery", "rich embroidery"}, "embroidery_level", "heavy", "embroidery"),
            ({"subtle embroidery", "light embroidery", "some embroidery"},
             "embroidery_level", "subtle", "embroidery"),
        ]
        applied_attrs: set[str] = set()
        for triggers, attr, value, label in rules:
            if any(t in lower for t in triggers) and attr and attr not in applied_attrs:
                setattr(state, attr, value)
                applied_attrs.add(attr)
                changes.append(f"Changed {label} to {value}")

        if "traditional" in lower:
            state.traditional_modern_balance = min(100, state.traditional_modern_balance + 25)
            changes.append("Shifted balance toward traditional (+25)")
        if "modern" in lower or "western" in lower:
            state.traditional_modern_balance = max(0, state.traditional_modern_balance - 25)
            changes.append("Shifted balance toward modern (-25)")
        if "formal" in lower:
            state.formality = min(5, state.formality + 1)
            changes.append(f"Increased formality to {state.formality}/5")
        if "casual" in lower and "smart-casual" not in lower:
            state.formality = max(1, state.formality - 1)
            changes.append(f"Eased formality to {state.formality}/5")

        import re as _re

        m = _re.search(r"(?:under|below|max(?:imum)?|budget of|within)\s*(?:₹|rs\.?|inr)?\s*([0-9][0-9,]*)", lower)
        if m:
            value = int(m.group(1).replace(",", ""))
            state.target_budget_inr = value
            changes.append(f"Set target budget to ₹{value:,}")

        reply = "Done! " + "; ".join(changes) if changes else \
            "Here's your current design — tell me what you'd like to change."
        image_prompt = (
            f"Fashion concept illustration of a {state.describe()}, studio lighting, "
            "elegant editorial fashion photography style, clean background."
        )
        return DesignTurnResponse(
            reply=reply,
            updated_design=state,
            changes=changes,
            image_prompt=image_prompt,
        )

    # ---- Embeddings -----------------------------------------------------
    def embed(self, texts: list[str]) -> list[list[float]]:
        # Deterministic pseudo-embeddings; replaced by real model when configured.
        vectors = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            vec = [b / 255.0 for b in h[:32]]
            vectors.append(vec)
        return vectors

    # ---- Voice ----------------------------------------------------------
    def transcribe(self, *, audio_bytes: bytes, language: str = "en") -> dict:
        """Deterministic dev stub — real STT arrives with a configured provider."""
        return {
            "text": "Voice note captured (dev mode: connect an STT provider for transcripts).",
            "language": language,
            "duration_seconds": max(1, len(audio_bytes) // 16000),
        }

    # ---- Wardrobe -------------------------------------------------------
    def recommend_from_wardrobe(self, *, occasion: str | None, budget_inr: int | None,
                                wardrobe_summary: list[dict],
                                style_context: dict | None = None) -> RecommendationResult:
        """Deterministic closet combination via the shared pure engine."""
        from ai.providers.closet import pick_combination

        seed = f"{occasion}|{budget_inr}|{len(wardrobe_summary)}"
        if style_context:
            seed += "|" + ",".join(style_context.get("preferred_styles", []))
        _, result = pick_combination(wardrobe_summary, occasion=occasion,
                                     budget_inr=budget_inr, seed=seed)
        return result
