import pytest

pytestmark = pytest.mark.django_db


def test_mock_analysis_validates(user):
    from ai.providers.mock import MockAIProvider
    from ai.schemas import ImageAnalysis

    result = MockAIProvider().analyze_image(image_bytes=b"\xff\xd8\xff\xe0fakejpeg", occasion="wedding")
    assert isinstance(result, ImageAnalysis)
    assert len(result.detected_clothing) > 0
    assert all(s.hex.startswith("#") for s in result.dominant_colors)


def test_mock_recommendation_respects_budget():
    from ai.providers.mock import MockAIProvider
    from ai.schemas import RecommendationResult

    result = MockAIProvider().recommend(analysis=None, occasion="office", budget_inr=2500)
    assert isinstance(result, RecommendationResult)
    assert result.budget_total_inr == 2500
    total_allocated = sum(line.amount_inr for line in result.budget_allocation)
    assert total_allocated == 2500


def test_designer_turn_applies_color_change():
    from ai.providers.mock import MockAIProvider
    from ai.schemas import DesignState

    state = DesignState(base_color="ivory")
    turn = MockAIProvider().design_turn(message="Make it emerald green", design_state=state)
    assert turn.updated_design.base_color == "emerald-green"
    assert any("color" in c for c in turn.changes)


def test_designer_turn_budget_extraction():
    from ai.providers.mock import MockAIProvider

    turn = MockAIProvider().design_turn(message="Design a kurta under ₹4,500", design_state=None)
    assert turn.updated_design.target_budget_inr == 4500


def test_safety_filter_blocks_out_of_scope():
    from ai.safety import check_input_safety
    from core.exceptions import AppError

    with pytest.raises(AppError) as exc:
        check_input_safety("Can you diagnose my skin disease?")
    assert exc.value.code == "ai_out_of_scope"
    check_input_safety("Design me a navy kurta for Diwali")  # must pass


def test_orchestrator_caches_identical_requests(user):
    from ai import orchestrator

    r1 = orchestrator.recommend_outfit(user=user, occasion="party", budget_inr=3000)
    r2 = orchestrator.recommend_outfit(user=user, occasion="party", budget_inr=3000)
    assert r1.headline == r2.headline


def test_duplicate_inflight_request_rejected(user, settings):
    # Simulate an in-flight request marker.
    from django.core.cache import cache

    from ai.orchestrator import _request_hash
    from core.exceptions import AppError

    rh = _request_hash("recommend", "party", None, "", {}, None)
    cache.set(f"ai:inflight:stylist_recommend:{rh}", True, 30)
    with pytest.raises(AppError) as exc:
        orchestrator_dup_check(user, rh)
    assert exc.value.code == "duplicate_request"


def orchestrator_dup_check(user, rh):
    """Invoke the duplicate gate directly."""
    from ai.orchestrator import _cached_or_duplicate

    _cached_or_duplicate("stylist_recommend", rh)
    _cached_or_duplicate("stylist_recommend", rh)  # second call within window raises


def test_quota_enforcement_uses_entitlements(user):
    from unittest.mock import patch

    import pytest

    from ai.models import AIUsageLog
    from ai.orchestrator import enforce_quota
    from core.exceptions import AppError
    from subscriptions.services import Entitlements

    ent = Entitlements(tier=None, ai_text_daily_limit=1, ai_image_monthly_limit=2,
                       max_saved_looks=10, wardrobe_item_limit=15,
                       designer_chat_enabled=False, customization_requests_enabled=False)
    AIUsageLog.objects.create(user=user, feature=AIUsageLog.Feature.STYLIST_RECOMMEND,
                              provider="mock", status=AIUsageLog.Status.SUCCESS)
    with patch("subscriptions.services.get_entitlements", return_value=ent):
        with pytest.raises(AppError) as exc:
            enforce_quota(user=user, scope="ai_text")
        assert exc.value.code == "quota_exceeded"
