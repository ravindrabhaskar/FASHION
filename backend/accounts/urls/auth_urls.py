from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts import views

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="auth-register"),
    path("login", views.LoginView.as_view(), name="auth-login"),
    path("refresh", TokenRefreshView.as_view(), name="auth-refresh"),
    path("social", views.SocialLoginView.as_view(), name="auth-social"),
    path("otp/request", views.RequestOTPView.as_view(), name="auth-otp-request"),
    path("otp/verify", views.VerifyOTPLoginView.as_view(), name="auth-otp-verify"),
    path("logout", views.LogoutView.as_view(), name="auth-logout"),
    path("logout-all", views.LogoutAllDevicesView.as_view(), name="auth-logout-all"),
    path("me", views.MeView.as_view(), name="auth-me"),
    path("password/change", views.ChangePasswordView.as_view(), name="auth-password-change"),
    path("password/forgot", views.ForgotPasswordView.as_view(), name="auth-password-forgot"),
    path("password/reset", views.ResetPasswordView.as_view(), name="auth-password-reset"),
    path("delete-account", views.DeleteAccountView.as_view(), name="auth-delete-account"),
    path("sessions", views.SessionsView.as_view(), name="auth-sessions"),
]
