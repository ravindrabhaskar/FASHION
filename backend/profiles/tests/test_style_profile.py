import pytest

pytestmark = pytest.mark.django_db


def test_style_profile_get(authed_api):
    response = authed_api.get("/api/v1/profile/style")
    assert response.status_code == 200
    assert response.json()["data"]["completion"] == 0


def test_progressive_patch_updates_completion(authed_api):
    patch = {"preferred_styles": ["minimal", "classic"], "favorite_colors": ["navy"]}
    response = authed_api.patch("/api/v1/profile/style", patch, format="json")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["completion"] >= 30


def test_invalid_occasion_rejected(authed_api):
    response = authed_api.patch("/api/v1/profile/style",
                                {"common_occasions": ["nonexistent-occasion"]}, format="json")
    assert response.status_code == 400


def test_budget_min_gt_max_rejected(authed_api):
    response = authed_api.patch("/api/v1/profile/style",
                                {"budget_min": 5000, "budget_max": 1000}, format="json")
    assert response.status_code == 400


def test_onboarding_status_flow(authed_api):
    authed_api.patch("/api/v1/profile/style", {
        "preferred_styles": ["minimal"],
        "favorite_colors": ["navy"],
        "fit_preference": "REGULAR",
        "budget_max": 5000,
        "common_occasions": ["office", "casual"],
        "clothing_preferences": {"shirts": True},
    }, format="json")

    status_response = authed_api.get("/api/v1/profile/onboarding-status")
    data = status_response.json()["data"]
    assert data["completed"] is True
    assert data["completion_percent"] == 100
