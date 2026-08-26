"""Master occasion registry — single source of truth for occasions across domains.

Pure data (no model imports) so any app can depend on it safely.
PRD §9: wedding, reception, engagement, festival, office, interview, college,
party, date, dinner, casual, travel, beach, business meeting, formal & cultural.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OccasionSpec:
    slug: str
    label: str
    formality: int  # 1=very casual ... 5=black-tie
    description: str
    palette_bias: tuple[str, ...]  # color families that work well by default
    keywords: tuple[str, ...] = ()


OCCASIONS: dict[str, OccasionSpec] = {
    spec.slug: spec
    for spec in (
        OccasionSpec("wedding", "Wedding", 5, "Traditional or formal celebration wear",
                     ("jewel", "gold", "pastel", "rich-red"), ("wedding", "shaadi", "bride", "groom")),
        OccasionSpec("reception", "Reception", 4, "Evening reception elegance",
                     ("navy", "gold", "wine"), ("reception",)),
        OccasionSpec("engagement", "Engagement", 4, "Semi-formal festive celebration",
                     ("blush", "champagne", "sage"), ("engagement", "roka")),
        OccasionSpec("festival", "Festival", 3, "Festive cultural dressing — Diwali, Eid, Sankranti",
                     ("marigold", "deep-green", "bright-pink"), ("diwali", "eid", "festival", "pongal")),
        OccasionSpec("office", "Office", 3, "Polished everyday professional",
                     ("navy", "grey", "white", "sky-blue"), ("office", "work")),
        OccasionSpec("interview", "Interview", 4, "Sharp, trustworthy and understated",
                     ("navy", "charcoal", "white"), ("interview", "job")),
        OccasionSpec("college", "College", 1, "Comfortable everyday campus style",
                     ("denim-blue", "white", "olive"), ("college", "campus", "class")),
        OccasionSpec("party", "Party", 3, "Fun, expressive evening looks",
                     ("black", "metallic", "bold-purple"), ("party", "club", "night out")),
        OccasionSpec("date", "Date", 3, "Effortlessly attractive, warm tones",
                     ("burgundy", "cream", "dusty-rose"), ("date", "dinner date")),
        OccasionSpec("dinner", "Dinner", 3, "Smart-casual dining elegance",
                     ("ink-blue", "camel", "black"), ("dinner", "restaurant")),
        OccasionSpec("casual", "Casual", 1, "Relaxed everyday comfort",
                     ("neutral", "denim-blue", "white"), ("casual", "weekend", "errands")),
        OccasionSpec("travel", "Travel", 2, "Practical layers with easy polish",
                     ("khaki", "grey", "navy"), ("travel", "airport", "trip")),
        OccasionSpec("beach", "Beach", 1, "Airy fabrics, sun-friendly shades",
                     ("aqua", "coral", "sand"), ("beach", "goa", "vacation")),
        OccasionSpec("business-meeting", "Business Meeting", 4, "Confident boardroom presence",
                     ("charcoal", "navy", "steel-grey"), ("meeting", "business", "client")),
        OccasionSpec("formal", "Formal Event", 5, "Black-tie and formal gatherings",
                     ("black", "midnight", "silver"), ("formal", "gala", "award")),
        OccasionSpec("cultural", "Cultural Event", 4, "Regional traditional attire done right",
                     ("ivory-gold", "temple-red", "indigo"), ("cultural", "traditional", "puja")),
    )
}

OCCASION_CHOICES = [(slug, spec.label) for slug, spec in OCCASIONS.items()]


def get_occasion(slug: str) -> OccasionSpec | None:
    return OCCASIONS.get((slug or "").strip().lower())
