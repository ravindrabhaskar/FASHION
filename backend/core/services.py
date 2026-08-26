"""Runtime configuration access: system config values + feature flags with safe defaults."""

from typing import Any

from core.models import FeatureFlag, SystemConfig

# Defaults ensure the platform works before an admin configures anything.
DEFAULTS: dict[str, Any] = {
    "ai.text_daily_limit_free": 5,
    "ai.image_monthly_limit_free": 3,
    "ai.cache_ttl_seconds": 3600,
    "ai.duplicate_window_seconds": 30,
    "ai.cost_per_1k_input_tokens": {"mock": 0.0, "gpt-4o-mini": 0.00015},
    "ai.cost_per_1k_output_tokens": {"mock": 0.0, "gpt-4o-mini": 0.0006},
    "marketplace.commission_percent": 12,
    # FashionXP economy (admin-tunable, PRD §16–18)
    "xp.post_created": 10,
    "xp.item_added": 5,
    "xp.outfit_saved": 4,
    "xp.designer_turn": 2,
    "xp.like_received": 2,
    "xp.comment_written": 3,
    "xp.follow_received": 3,
    "xp.challenge_completed": 50,
    "xp.daily_earn_cap": 100,
}


def get_config(key: str, default: Any = None) -> Any:
    from django.core.cache import cache

    cache_key = f"syscfg:{key}"
    value = cache.get(cache_key)
    if value is None:
        try:
            value = SystemConfig.objects.get(key=key).value
        except SystemConfig.DoesNotExist:
            value = DEFAULTS.get(key, default)
        cache.set(cache_key, value, 300)
    return value


def set_config(key: str, value: Any, *, updated_by=None) -> SystemConfig:
    obj, _ = SystemConfig.objects.update_or_create(
        key=key, defaults={"value": value, "updated_by": updated_by}
    )
    from django.core.cache import cache

    cache.delete(f"syscfg:{key}")
    return obj


def is_enabled(flag_key: str, default: bool = False) -> bool:
    """Feature flag lookup; falls back to `default` when unset."""
    from django.core.cache import cache

    cache_key = f"flag:{flag_key}"
    enabled = cache.get(cache_key)
    if enabled is None:
        enabled = FeatureFlag.objects.filter(key=flag_key).values_list("enabled", flat=True).first()
        if enabled is None:
            enabled = default
        cache.set(cache_key, enabled, 120)
    return bool(enabled)


MAJOR_FLAGS = [
    ("ai_designer", "Conversational AI Fashion Designer"),
    ("wardrobe", "Digital Wardrobe"),
    ("social_feed", "Social Fashion Network"),
    ("fashionxp", "FashionXP rewards"),
    ("challenges", "FashionXP Challenges"),
    ("marketplace", "Local fashion marketplace"),
    ("creator_campaigns", "Brand-creator campaigns"),
    ("virtual_tryon", "Virtual try-on (advanced AI)"),
]
