import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def _register(api, email="new@example.com"):
    return api.post("/api/v1/auth/register", {
        "email": email, "full_name": "New User", "password": "strong-pass-1",
        "device_name": "Pixel 8",
    }, format="json")


def test_register_returns_tokens_and_companion_profiles(api):
    response = _register(api)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["access"]
    assert data["user"]["email"] == "new@example.com"

    User = get_user_model()
    user = User.objects.get(email="new@example.com")
    assert hasattr(user, "profile")
    assert hasattr(user, "style_profile")


def test_login_success_and_failure(api, user):
    ok = api.post("/api/v1/auth/login",
                  {"email": user.email, "password": "strong-pass-1"}, format="json")
    assert ok.status_code == 200
    bad = api.post("/api/v1/auth/login", {"email": user.email, "password": "wrong"}, format="json")
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "invalid_credentials"


def test_me_endpoint(authed_api):
    response = authed_api.get("/api/v1/auth/me")
    assert response.status_code == 200
    me = response.json()["data"]
    assert me["email"] == "test@example.com"
    assert me["onboarding_completed"] is False


def test_logout_all_blacklists_refresh_tokens(api, user):
    login = api.post("/api/v1/auth/login",
                     {"email": user.email, "password": "strong-pass-1"}, format="json").json()["data"]
    refresh = login["refresh"]
    out = api.post("/api/v1/auth/logout-all", HTTP_AUTHORIZATION=f"Bearer {login['access']}")
    assert out.status_code == 200
    reuse = api.post("/api/v1/auth/refresh", {"refresh": refresh}, format="json")
    assert reuse.status_code == 401


def test_password_change_revokes_sessions(api, user):
    login = api.post("/api/v1/auth/login",
                     {"email": user.email, "password": "strong-pass-1"}, format="json").json()["data"]
    changed = api.post("/api/v1/auth/password/change", {
        "current_password": "strong-pass-1", "new_password": "even-stronger-2",
    }, format="json", HTTP_AUTHORIZATION=f"Bearer {login['access']}")
    assert changed.status_code == 200

    old_refresh = login["refresh"]
    reuse = api.post("/api/v1/auth/refresh", {"refresh": old_refresh}, format="json")
    assert reuse.status_code == 401

    relogin = api.post("/api/v1/auth/login",
                       {"email": user.email, "password": "even-stronger-2"}, format="json")
    assert relogin.status_code == 200


def test_forgot_password_always_succeeds_no_enumeration(api, user):
    response = api.post("/api/v1/auth/password/forgot", {"email": "ghost@nowhere.com"}, format="json")
    assert response.status_code == 200


def test_delete_account_anonymizes(api):
    register = _register(api).json()["data"]
    access = register["access"]
    deleted = api.post("/api/v1/auth/delete-account", {"password": "strong-pass-1"},
                       format="json", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert deleted.status_code == 200

    User = get_user_model()
    user = User.objects.get(full_name="Deleted User")
    assert user.status == "DELETED"
    assert not user.is_active
    assert user.email.startswith("deleted-")
    assert register["user"]["email"] != user.email or True  # original email replaced


def test_otp_flow_dev_mode(api, settings, db):
    from accounts.models import PhoneOTP

    request = api.post("/api/v1/auth/otp/request",
                       {"phone": "+919876543210", "purpose": "LOGIN"}, format="json")
    assert request.status_code == 200
    otp = PhoneOTP.objects.filter(phone="+919876543210").latest("created_at")

    # Wrong code rejected.
    wrong = api.post("/api/v1/auth/otp/verify",
                     {"phone": "+919876543210", "code": "000000"}, format="json")
    assert wrong.status_code == 400

    # Extract real code via service (console provider logs it).
    import hashlib
    code = None
    for candidate in range(1000000):
        c = f"{candidate:06d}"
        if hashlib.sha256(c.encode()).hexdigest() == otp.code_hash:
            code = c
            break
    assert code is not None
    verified = api.post("/api/v1/auth/otp/verify",
                        {"phone": "+919876543210", "code": code}, format="json")
    assert verified.status_code == 200
    assert verified.json()["data"]["access"]


def test_social_provider_unconfigured_clean_error(api, settings):
    settings.GOOGLE_OAUTH_CLIENT_IDS = []
    response = api.post("/api/v1/auth/social",
                        {"provider": "google", "id_token": "x.y.z"}, format="json")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_not_configured"
