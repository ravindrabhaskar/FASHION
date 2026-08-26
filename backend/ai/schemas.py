"""Structured, validated AI output schemas.

Every provider must return data conforming to these models; the orchestrator
validates before anything reaches the client (PRD §9/§31 response validation).
"""
from typing import Literal

from pydantic import BaseModel, Field


class ColorSwatch(BaseModel):
    name: str
    hex: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    role: Literal["primary", "secondary", "accent", "neutral"]


class GarmentSpec(BaseModel):
    category: str  # e.g. "kurta", "shirt"
    description: str
    color: str = ""
    fabric: str = ""
    pattern: str = ""
    details: list[str] = Field(default_factory=list)  # sleeves/collar/embroidery notes


class OutfitComponent(BaseModel):
    slot: str  # top | bottom | outerwear | footwear | accessory_1 ...
    item: GarmentSpec


class BudgetLine(BaseModel):
    component: str
    amount_inr: int = Field(ge=0)


class RecommendationResult(BaseModel):
    """The stylist 'wow' payload: complete, structured, validated."""

    headline: str
    explanation: str
    occasion_fit_notes: str = ""
    palette: list[ColorSwatch] = Field(default_factory=list)
    outfit_components: list[OutfitComponent] = Field(default_factory=list)
    accessories: list[str] = Field(default_factory=list)
    footwear_note: str = ""
    budget_total_inr: int | None = None
    budget_allocation: list[BudgetLine] = Field(default_factory=list)
    styling_tips: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    alternatives: list[str] = Field(default_factory=list)
    # Wardrobe-based looks: ids of the user's items used in this combination.
    used_item_ids: list[str] = Field(default_factory=list)


class ImageAnalysis(BaseModel):
    """Neutral fashion-focused photo analysis — no body judgments, no identity inference."""

    detected_clothing: list[GarmentSpec] = Field(default_factory=list)
    dominant_colors: list[ColorSwatch] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    formality_level: int = Field(default=3, ge=1, le=5)
    occasion_compatibility: list[str] = Field(default_factory=list)
    summary: str = ""


class DesignState(BaseModel):
    """Conversational designer state — mutated turn by turn, never regenerated blindly."""

    garment_type: str = "kurta-set"          # kurta-set | saree | dress | shirt-trouser | lehenga | ...
    base_color: str = "ivory"
    accent_color: str = "gold"
    fabric: str = "cotton-silk"
    sleeve_style: str = "three-quarter"
    collar_neckline: str = "mandarin"
    length: str = "ankle"                    # for kurtas/dresses
    pattern: str = "solid"
    embroidery_level: Literal["none", "subtle", "moderate", "heavy"] = "none"
    traditional_modern_balance: int = Field(default=50, ge=0, le=100)
    formality: int = Field(default=3, ge=1, le=5)
    weather_suitability: str = "all-season"  # hot | humid | cool | all-season
    target_budget_inr: int | None = None
    accessories: list[str] = Field(default_factory=list)
    notes: str = ""

    def describe(self) -> str:
        bits = [
            f"{self.garment_type.replace('-', ' ')} in {self.base_color}"
            + (f" with {self.accent_color} accents" if self.accent_color else ""),
            f"{self.fabric}", f"{self.sleeve_style} sleeves", f"{self.collar_neckline} neckline",
            f"{self.length} length", self.pattern,
            f"embroidery: {self.embroidery_level}",
            f"style balance {self.traditional_modern_balance}/100 (traditional→modern)",
            f"formality {self.formality}/5", f"weather: {self.weather_suitability}",
        ]
        if self.target_budget_inr:
            bits.append(f"budget ₹{self.target_budget_inr}")
        return "; ".join(bits)


class DesignTurnResponse(BaseModel):
    """Result of one conversational designer turn."""

    reply: str
    updated_design: DesignState
    changes: list[str] = Field(default_factory=list)  # human-readable change log for this turn
    image_prompt: str = ""
