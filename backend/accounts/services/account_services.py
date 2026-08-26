"""Account services: OTP delivery, password reset, social sign-in token verification."""
import hashlib
import hmac
import secrets
from dataclasses import dataclass

import httpx
import jwt
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.utils import timezone

from accounts.models import PhoneOTP, UserStatus
from core.exceptions import AppError

# ---- SMS provider abstraction ---------------------------------------------

def send_sms(phone: str, message: str) -> None:
    provider = settings.SMS_PROVIDER
    if provider == "console":
        # Dev: surface the code in logs instead of a real gateway.
        import logging

        logging.getLogger("accounts.otp").info("SMS to %s: %s", phone, message)
        return
    raise AppError(f"SMS provider '{provider}' is not configured", code="sms_provider_missing", status_code=503)


# ---- OTP -------------------------------------------------------------------

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 45


@dataclass
class IssuedOTP:
    expires_at: timezone.datetime
    dev_code: str | None = None  # only populated in DEBUG for local testing


def issue_otp(phone: str, purpose: PhoneOTP.Purpose) -> IssuedOTP:
    cooldown_key = f"otp:cooldown:{phone}:{purpose}"
    if cache.get(cooldown_key):
        raise AppError("Please wait before requesting another code.", code="otp_cooldown")

    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = PhoneOTP.objects.create(
        phone=phone,
        purpose=purpose,
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        expires_at=timezone.now() + timezone.timedelta(minutes=OTP_TTL_MINUTES),
    )
    cache.set(cooldown_key, True, OTP_RESEND_COOLDOWN_SECONDS)
    send_sms(phone, f"FashionXP: your verification code is {code}. Valid {OTP_TTL_MINUTES} minutes.")
    return IssuedOTP(expires_at=otp.expires_at, dev_code=code if settings.DEBUG else None)


def verify_otp(phone: str, purpose: PhoneOTP.Purpose, code: str) -> bool:
    otp = (
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if not otp or otp.is_expired or otp.attempts >= OTP_MAX_ATTEMPTS:
        return False
    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    if not hmac.compare_digest(otp.code_hash, hashlib.sha256(code.encode()).hexdigest()):
        return False
    otp.consumed_at = timezone.now()
    otp.save(update_fields=["consumed_at"])
    return True


# ---- Password reset ---------------------------------------------------------
# Signed short-lived tokens via Django signing; no extra DB round-trip to validate.

RESET_TOKEN_MAX_AGE_SECONDS = 60 * 30


def make_password_reset_token(user) -> str:
    return signing.dumps({"uid": str(user.id)}, salt="fashionxp.password.reset.v1", compress=True)


def resolve_password_reset_token(token: str):
    from django.contrib.auth import get_user_model

    try:
        data = signing.loads(token, salt="fashionxp.password.reset.v1", max_age=RESET_TOKEN_MAX_AGE_SECONDS)
    except signing.BadSignature:
        return None
    return (
        get_user_model()
        .objects.filter(id=data.get("uid"), status=UserStatus.ACTIVE)
        .first()
    )


# ---- Social sign-in (Google / Apple) ---------------------------------------

JWKS_CACHE_KEY = "accounts:jwks:{provider}"
JWKS_URLS = {
    "google": "https://www.googleapis.com/oauth2/v3/certs",
    "apple": "https://appleid.apple.com/auth/keys",
}
ID_TOKEN_ISSUERS = {"google": "https://accounts.google.com", "apple": "https://appleid.apple.com"}


def verify_social_id_token(provider: str, id_token: str) -> dict:
    """Verify an external OIDC id-token against the provider JWKS.

    Returns claims {sub, email, name} on success; raises AppError otherwise.
    Audience is validated against the first configured client id per provider.
    """
    if provider not in JWKS_URLS:
        raise AppError("Unsupported sign-in provider.", code="unsupported_provider")

    allowed_audiences = {
        "google": settings.GOOGLE_OAUTH_CLIENT_IDS,
        "apple": settings.APPLE_OAUTH_CLIENT_IDS,
    }[provider]
    if not allowed_audiences:
        raise AppError(
            f"{provider.title()} sign-in is not configured on this server.",
            code="provider_not_configured",
            status_code=503,
        )

    jwks = cache.get(JWKS_CACHE_KEY.format(provider=provider))
    if not jwks:
        try:
            resp = httpx.get(JWKS_URLS[provider], timeout=10)
            resp.raise_for_status()
            jwks = resp.json()
        except httpx.HTTPError as exc:
            raise AppError("Could not reach sign-in provider.", code="provider_unavailable", status_code=502) from exc
        cache.set(JWKS_CACHE_KEY.format(provider=provider), jwks, 3600)

    jwk_client = jwt.PyJWKClient(jwks)
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=allowed_audiences[0],
            issuer=ID_TOKEN_ISSUERS[provider],
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AppError("Sign-in token was invalid or expired.", code="invalid_id_token") from exc

    email = claims.get("email")
    if not email:
        raise AppError("Sign-in did not share an email address.", code="email_not_shared")
    return {"sub": claims["sub"], "email": email.lower(), "name": claims.get("name", "")}
