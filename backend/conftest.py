import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(email="test@example.com", password="strong-pass-1",
                                    full_name="Test User")


@pytest.fixture
def authed_api(api, user):
    response = api.post("/api/v1/auth/login", {"email": user.email, "password": "strong-pass-1"},
                        format="json")
    token = response.json()["data"]["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


@pytest.fixture
def occasion_seeded(db):
    from fashion.models import Occasion

    return Occasion.objects.create(slug="wedding", label="Wedding", formality=5)
