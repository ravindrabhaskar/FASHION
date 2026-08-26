"""AI Orchestrator — the ONLY path to any AI provider (PRD §31).

Responsibilities:
- Provider routing & fallback (settings.AI_PROVIDER; falls back to mock on failure)
- Structured output validation via pydantic schemas
- Safety checks (input gate + output sanitation)
- Duplicate-request detection + response caching
- Usage/cost/latency ledger per call
"""
import hashlib
import json
import logging
import time

from django.core.cache import cache
from django.utils import timezone

from ai import safety
from ai.models import AIUsageLog
from ai.providers.image_gen import MockImageProvider, OpenAIImageProvider
from ai.providers.mock import MockAIProvider
from core.exceptions import AppError
from core.services import get_config

logger = logging.getLogger(__name__)


class MockProviderFallback:
    """Internal marker: real provider failed; we served a graceful mock result."""

    pass


def _provider():
    from django.conf import settings as dj_settings

    if dj_settings.AI_PROVIDER == "openai-compatible" and dj_settings.OPENAI_API_KEY:
        from ai.providers.openai_compat import OpenAICompatibleProvider

        return OpenAICompatibleProvider()
    return MockAIProvider()


def _image_provider():
    from django.conf import settings as dj_settings

    if dj_settings.AI_PROVIDER == "openai-compatible" and dj_settings.OPENAI_API_KEY:
        return OpenAIImageProvider()
    return MockImageProvider()


def _request_hash(*parts) -> str:
    canonical = json.dumps(parts, default=str, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    in_rate = (get_config("ai.cost_per_1k_input_tokens") or {}).get(model, 0.0)
    out_rate = (get_config("ai.cost_per_1k_output_tokens") or {}).get(model, 0.0)
    return round(input_tokens / 1000 * float(in_rate) + output_tokens / 1000 * float(out_rate), 6)


def _log_usage(**kwargs) -> None:
    try:
        AIUsageLog.objects.create(**kwargs)
    except Exception:  # noqa: BLE001 - never break the request over telemetry
        logger.exception("Failed to write AIUsageLog")


def _cached_or_duplicate(feature: str, request_hash: str):
    """Returns (result, cache_hit, duplicate_flag). None result = proceed."""
    dup_window = int(get_config("ai.duplicate_window_seconds", 30))
    cache_key = f"ai:resp:{feature}:{request_hash}"
    inflight_key = f"ai:inflight:{feature}:{request_hash}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached, True, False
    if cache.get(inflight_key):
        raise AppError(
            "That's already being generated — one moment!",
            code="duplicate_request",
            status_code=429,
        )
    cache.set(inflight_key, True, dup_window)
    return None, False, False


def _store_cache(feature: str, request_hash: str, value) -> None:
    ttl = int(get_config("ai.cache_ttl_seconds", 3600))
    cache.set(f"ai:resp:{feature}:{request_hash}", value, ttl)


# ---- Public API --------------------------------------------------------------

def _user_language(user) -> str:
    try:
        return getattr(getattr(user, "profile", None), "language", "") or "en"
    except Exception:  # noqa: BLE001
        return "en"


def analyze_image(*, user, image_bytes: bytes, occasion: str | None = None,
                  user_notes: str = ""):
    """Photo → validated ImageAnalysis."""
    safety.check_input_safety(user_notes)
    rh = _request_hash("analyze", len(image_bytes), occasion or "", user_notes.strip().lower())

    cached, hit, _ = _cached_or_duplicate("stylist_analysis", rh)
    if cached is not None:
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_ANALYSIS, provider=_provider().name,
                   status=AIUsageLog.Status.CACHED, cache_hit=True, request_hash=rh)
        return cached

    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.analyze_image(image_bytes=image_bytes, occasion=occasion, user_notes=user_notes)
        latency = int((time.monotonic() - start) * 1000)
        _store_cache("stylist_analysis", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_ANALYSIS, provider=provider.name,
                   model=getattr(provider, "model_name", ""), latency_ms=latency, request_hash=rh,
                   estimated_cost_usd=_estimate_cost("", 0, 0))
        return result
    except AppError:
        raise
    except Exception as exc:  # fallback keeps the product alive
        logger.exception("Vision analysis failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("Photo analysis is unavailable right now. Please retry.",
                           code="ai_unavailable", status_code=503) from exc
        result = MockAIProvider().analyze_image(image_bytes=image_bytes, occasion=occasion,
                                                user_notes=user_notes)
        _store_cache("stylist_analysis", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_ANALYSIS, provider=f"{provider.name}+mock-fallback",
                   status=AIUsageLog.Status.FAILED, error=str(exc)[:255], request_hash=rh)
        return result


def recommend_outfit(*, user, analysis=None, occasion=None, budget_inr=None,
                     user_notes="", style_context=None):
    """Analysis + context → validated RecommendationResult."""
    safety.check_input_safety(user_notes)
    ctx_key = [
        occasion, budget_inr, (user_notes or "").strip().lower(),
        style_context or {},
        analysis.summary if analysis else None,
    ]
    rh = _request_hash("recommend", *ctx_key)

    cached, hit, _ = _cached_or_duplicate("stylist_recommend", rh)
    if cached is not None:
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND, provider=_provider().name,
                   status=AIUsageLog.Status.CACHED, cache_hit=True, request_hash=rh)
        return cached

    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.recommend(analysis=analysis, occasion=occasion, budget_inr=budget_inr,
                                    user_notes=user_notes, style_context=style_context,
                                    language=_user_language(user))
        latency = int((time.monotonic() - start) * 1000)
        _store_cache("stylist_recommend", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND, provider=provider.name,
                   latency_ms=latency, request_hash=rh)
        return result
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Recommendation failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("Styling service is unavailable right now. Please retry.",
                           code="ai_unavailable", status_code=503) from exc
        result = MockAIProvider().recommend(analysis=analysis, occasion=occasion,
                                            budget_inr=budget_inr, user_notes=user_notes,
                                            style_context=style_context)
        _store_cache("stylist_recommend", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND,
                   provider=f"{provider.name}+mock-fallback", status=AIUsageLog.Status.FAILED,
                   error=str(exc)[:255], request_hash=rh)
        return result


def designer_turn(*, user, conversation_history: list[dict], message: str,
                  current_design=None):
    """One conversational design turn → DesignTurnResponse (validated)."""
    safety.check_input_safety(message)
    history_tail = conversation_history[-6:]
    rh = _request_hash("design_turn", message.strip().lower(),
                       current_design.model_dump() if current_design else None,
                       [m.get("content", "")[:120] for m in history_tail])

    cached, _, _ = _cached_or_duplicate("designer_chat", rh)
    if cached is not None:
        _log_usage(user=user, feature=AIUsageLog.Feature.DESIGNER_CHAT, provider=_provider().name,
                   status=AIUsageLog.Status.CACHED, cache_hit=True, request_hash=rh)
        return cached

    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.design_turn(message=message, design_state=current_design,
                                      language=_user_language(user))
        # Sanitize reply text defensively.
        result.reply = safety.sanitize_output_text(result.reply)[:1500]
        latency = int((time.monotonic() - start) * 1000)
        _store_cache("designer_chat", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.DESIGNER_CHAT, provider=provider.name,
                   latency_ms=latency, request_hash=rh)
        return result
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Designer turn failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("The AI designer is unavailable right now. Please retry.",
                           code="ai_unavailable", status_code=503) from exc
        result = MockAIProvider().design_turn(message=message, design_state=current_design)
        _store_cache("designer_chat", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.DESIGNER_CHAT,
                   provider=f"{provider.name}+mock-fallback", status=AIUsageLog.Status.FAILED,
                   error=str(exc)[:255], request_hash=rh)
        return result


def generate_outfit_image(*, prompt: str) -> dict:
    """Image generation payload for async workers. Returns raw bytes + metadata."""
    return _image_provider().generate(prompt=prompt)


def transcribe(*, user, audio_bytes: bytes, language: str = "en") -> dict:
    """Voice note → text via the configured STT provider (mock stub in dev)."""
    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.transcribe(audio_bytes=audio_bytes, language=language)
        latency = int((time.monotonic() - start) * 1000)
        _log_usage(user=user, feature=AIUsageLog.Feature.WARDROBE_EXTRACT,
                   provider=provider.name, model=getattr(provider, "model_name", ""),
                   latency_ms=latency, request_hash=_request_hash("transcribe", len(audio_bytes)))
        return result
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Transcription failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("Voice input is unavailable right now.",
                           code="ai_unavailable", status_code=503) from exc
        return MockAIProvider().transcribe(audio_bytes=audio_bytes, language=language)


def extract_wardrobe_attributes(*, user, image_bytes: bytes):
    """Wardrobe photo → validated ImageAnalysis (attribute extraction for closet items).

    Tracked under its own feature so it never consumes the stylist's daily quota.
    """
    rh = _request_hash("wardrobe_extract", len(image_bytes))

    cached, _, _ = _cached_or_duplicate("wardrobe_extract", rh)
    if cached is not None:
        _log_usage(user=user, feature=AIUsageLog.Feature.WARDROBE_EXTRACT,
                   provider=_provider().name, status=AIUsageLog.Status.CACHED,
                   cache_hit=True, request_hash=rh)
        return cached

    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.analyze_image(image_bytes=image_bytes, occasion=None, user_notes="")
        latency = int((time.monotonic() - start) * 1000)
        _store_cache("wardrobe_extract", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.WARDROBE_EXTRACT,
                   provider=provider.name, model=getattr(provider, "model_name", ""),
                   latency_ms=latency, request_hash=rh)
        return result
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Wardrobe extraction failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("Item analysis is unavailable right now. Please retry.",
                           code="ai_unavailable", status_code=503) from exc
        result = MockAIProvider().analyze_image(image_bytes=image_bytes, occasion=None,
                                                user_notes="")
        _store_cache("wardrobe_extract", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.WARDROBE_EXTRACT,
                   provider=f"{provider.name}+mock-fallback", status=AIUsageLog.Status.FAILED,
                   error=str(exc)[:255], request_hash=rh)
        return result


def recommend_from_wardrobe(*, user, occasion=None, budget_inr=None,
                            wardrobe_summary: list[dict] | None = None,
                            style_context: dict | None = None):
    """User's own wardrobe → validated RecommendationResult referencing their items."""
    summary = wardrobe_summary or []
    ctx_key = [occasion, budget_inr, sorted(i.get("id", "") for i in summary), style_context or {}]
    rh = _request_hash("wardrobe_recommend", *ctx_key)

    cached, _, _ = _cached_or_duplicate("wardrobe_recommend", rh)
    if cached is not None:
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND,
                   provider=_provider().name, status=AIUsageLog.Status.CACHED,
                   cache_hit=True, request_hash=rh)
        return cached

    start = time.monotonic()
    provider = _provider()
    try:
        result = provider.recommend_from_wardrobe(
            occasion=occasion, budget_inr=budget_inr,
            wardrobe_summary=summary, style_context=style_context,
        )
        latency = int((time.monotonic() - start) * 1000)
        _store_cache("wardrobe_recommend", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND,
                   provider=provider.name, latency_ms=latency, request_hash=rh)
        return result
    except AppError:
        raise
    except Exception as exc:
        logger.exception("Wardrobe recommendation failed; using mock fallback")
        if isinstance(provider, MockAIProvider):
            raise AppError("Closet styling is unavailable right now. Please retry.",
                           code="ai_unavailable", status_code=503) from exc
        result = MockAIProvider().recommend_from_wardrobe(
            occasion=occasion, budget_inr=budget_inr,
            wardrobe_summary=summary, style_context=style_context,
        )
        _store_cache("wardrobe_recommend", rh, result)
        _log_usage(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND,
                   provider=f"{provider.name}+mock-fallback", status=AIUsageLog.Status.FAILED,
                   error=str(exc)[:255], request_hash=rh)
        return result


# ---- Quota helpers -------------------------------------------------------

def count_recent_usage(user_id, feature: str, since) -> int:
    return AIUsageLog.objects.filter(
        user_id=user_id,
        feature=feature,
        created_at__gte=since,
        status__in=[AIUsageLog.Status.SUCCESS],
    ).count()


def today_start():
    return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)


def month_start():
    return timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def enforce_quota(*, user, scope: str) -> None:
    """Raise a friendly AppError when the user is out of AI quota.

    Centralized here so every AI endpoint shares identical behavior.
    """
    from subscriptions.services import assert_within_quota, get_entitlements

    ent = get_entitlements(user)
    if scope == "ai_text":
        used = count_recent_usage(user.id, AIUsageLog.Feature.STYLIST_RECOMMEND, today_start()) \
            + count_recent_usage(user.id, AIUsageLog.Feature.DESIGNER_CHAT, today_start())
        limit_scope = "ai_text"
    elif scope == "ai_image":
        used = count_recent_usage(user.id, AIUsageLog.Feature.OUTFIT_IMAGE, month_start())
        limit_scope = "ai_image"
    else:
        return
    try:
        assert_within_quota(ent, limit_scope, used)
    except Exception as exc:
        label = "daily AI stylist" if scope == "ai_text" else "monthly AI image"
        raise AppError(
            f"You've reached your {label} limit. Upgrade your plan or try again tomorrow.",
            code="quota_exceeded",
            details={"scope": limit_scope},
        ) from exc


# Backward-compat alias for tests that patch this.
def get_provider_for_feature(feature: str):
    return _provider()
