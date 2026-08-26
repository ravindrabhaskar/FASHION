"""Authentication endpoints: email/password, OTP, social, sessions, account lifecycle."""
import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone as dj_timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import DeviceSession, PhoneOTP, UserStatus
from accounts.serializers import (
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    MeSerializer,
    OTPRequestSerializer,
    OTPVerifyLoginSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    SocialLoginSerializer,
    UpdateMeSerializer,
)
from accounts.services.account_services import (
    issue_otp,
    make_password_reset_token,
    resolve_password_reset_token,
    verify_otp,
    verify_social_id_token,
)
from core.exceptions import AppError
from core.models import record_audit

logger = logging.getLogger(__name__)
User = get_user_model()

OTP_LOGIN_ATTEMPT_LIMIT_PER_HOUR = 10


def _client_meta(request) -> dict:
    meta = request.META
    ip = meta.get("HTTP_X_FORWARDED_FOR", meta.get("REMOTE_ADDR", ""))
    ip = ip.split(",")[0].strip() if ip else None
    return {"ip_address": ip or None, "user_agent": meta.get("HTTP_USER_AGENT", "")[:500]}


def _register_device_session(user, refresh_token: RefreshToken, request, device_name: str) -> None:
    DeviceSession.objects.create(
        user=user,
        jti=refresh_token.payload.get("jti", ""),
        device_name=device_name[:120],
        **_client_meta(request),
    )


def _token_pair_response(user, request, device_name: str = "") -> Response:
    refresh = RefreshToken.for_user(user)
    _register_device_session(user, refresh, request, device_name)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user).data,
        }
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _token_pair_response(user, request, device_name=request.data.get("device_name", ""))


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(serializer.validated_data["password"]):
            raise AppError("Email or password is incorrect.", code="invalid_credentials",
                           status_code=status.HTTP_401_UNAUTHORIZED)
        if user.status == UserStatus.SUSPENDED:
            raise AppError("This account has been suspended. Contact support.", code="account_suspended",
                           status_code=status.HTTP_403_FORBIDDEN)
        if user.status == UserStatus.DELETED:
            raise AppError("Email or password is incorrect.", code="invalid_credentials",
                           status_code=status.HTTP_401_UNAUTHORIZED)
        return _token_pair_response(user, request, device_name=request.data.get("device_name", ""))


class SocialLoginView(APIView):
    """Google/Apple sign-in: verifies the provider id-token server-side."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        claims = verify_social_id_token(
            serializer.validated_data["provider"], serializer.validated_data["id_token"]
        )
        user, created = User.objects.get_or_create(
            email=claims["email"],
            defaults={"full_name": claims["name"] or claims["email"].split("@")[0]},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        if user.status != UserStatus.ACTIVE:
            raise AppError("This account is not available.", code="account_unavailable",
                           status_code=status.HTTP_403_FORBIDDEN)
        return _token_pair_response(user, request)


class RequestOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        purpose = serializer.validated_data["purpose"]

        hourly_key = f"otp:hour:{phone}"
        attempts = int(cache.get(hourly_key, 0))
        if attempts >= OTP_LOGIN_ATTEMPT_LIMIT_PER_HOUR:
            raise AppError("Too many code requests. Try again later.", code="otp_rate_limited")
        cache.set(hourly_key, attempts + 1, 3600)

        issued = issue_otp(phone, purpose)
        payload = {"expires_at": issued.expires_at.isoformat()}
        if issued.dev_code:
            payload["dev_code"] = issued.dev_code  # DEBUG builds only
        return Response(payload)


class VerifyOTPLoginView(APIView):
    """Login (or auto-register) with a verified phone code."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = OTPVerifyLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        if not verify_otp(phone, PhoneOTP.Purpose.LOGIN, code):
            raise AppError("That code is invalid or expired.", code="invalid_otp")

        suffix = phone[-4:]
        user = (
            User.objects.filter(phone=phone).first()
            or User.objects.create_user(
                email=f"user-{phone.replace('+', '')}@phone.fashionxp.local",
                full_name=serializer.validated_data.get("full_name") or f"User {suffix}",
                phone=phone,
            )
        )
        if user.status != UserStatus.ACTIVE:
            raise AppError("This account is not available.", code="account_unavailable",
                           status_code=status.HTTP_403_FORBIDDEN)
        return _token_pair_response(user, request)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        DeviceSession.objects.filter(user=request.user).update(revoked_at=None)  # no-op keep rows
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllDevicesView(APIView):
    """Blacklists every outstanding refresh token for the user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        count = 0
        for token in OutstandingToken.objects.filter(user=request.user):
            _, created = BlacklistedToken.objects.get_or_create(token=token)
            count += int(created)
        now = dj_timezone.now()
        DeviceSession.objects.filter(user=request.user, revoked_at__isnull=True).update(revoked_at=now)
        record_audit(actor=request.user, action="auth.logout_all", target=request.user,
                     metadata={"tokens_blacklisted": count})
        return Response({"sessions_revoked": True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateMeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["current_password"]):
            raise AppError("Current password is incorrect.", code="wrong_password")
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        # Force re-login everywhere after a password change.
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        return Response({"changed": True})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"].lower()).first()
        if user and user.status == UserStatus.ACTIVE:
            token = make_password_reset_token(user)
            # Email delivery is abstracted; console backend logs it in dev.
            logger.info("Password reset link token generated for %s", user.email)
            reset_url = f"fashionxp://reset-password?token={token}"
            self._send_reset_email(user.email, reset_url)
        # Always succeed to avoid account enumeration.
        return Response({"sent": True})

    @staticmethod
    def _send_reset_email(to_email: str, reset_url: str) -> None:
        from django.conf import settings as dj_settings
        from django.core.mail import send_mail

        try:
            send_mail(
                subject="Reset your FashionXP password",
                message=f"Use this link within 30 minutes to reset your password:\n{reset_url}",
                from_email=dj_settings.DEFAULT_FROM_EMAIL
                if hasattr(dj_settings, "DEFAULT_FROM_EMAIL") else "no-reply@fashionxp.local",
                recipient_list=[to_email],
                fail_silently=True,
            )
        except Exception:  # pragma: no cover
            logger.exception("Failed sending reset email")


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = resolve_password_reset_token(serializer.validated_data["token"])
        if not user:
            raise AppError("Reset link is invalid or expired.", code="invalid_reset_token")
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        record_audit(actor=user, action="auth.password_reset", target=user)
        return Response({"reset": True})


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if user.has_usable_password() and not user.check_password(serializer.validated_data["password"]):
            raise AppError("Password is incorrect.", code="wrong_password")
        user.soft_delete_and_anonymize()
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        record_audit(action="account.deleted", target=user, metadata={"self_service": True})
        return Response({"deleted": True})


class SessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = DeviceSession.objects.filter(user=request.user, revoked_at__isnull=True)
        data = [
            {
                "id": str(s.id),
                "device_name": s.device_name or "Unknown device",
                "last_used_at": s.last_used_at,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
        return Response(data)
