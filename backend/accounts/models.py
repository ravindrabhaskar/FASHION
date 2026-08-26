import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    USER = "USER", "User"
    CREATOR = "CREATOR", "Creator"
    DESIGNER = "DESIGNER", "Designer"
    BRAND = "BRAND", "Brand"
    MODERATOR = "MODERATOR", "Moderator"
    ADMIN = "ADMIN", "Admin"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    DELETED = "DELETED", "Deleted"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password) if password else user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("role", UserRole.USER)
        return self._create(email, password, **extra)

    def create_superuser(self, email: str, password: str, **extra):
        extra.setdefault("role", UserRole.SUPER_ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._create(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True, default="")
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    status = models.CharField(max_length=12, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    avatar = models.URLField(blank=True, default="")
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)  # mirrors status != DELETED/SUSPENDED for auth checks
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=["role"]), models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    # ---- helpers ---------------------------------------------------------
    @property
    def is_admin_level(self) -> bool:
        return self.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}

    @property
    def is_moderator_level(self) -> bool:
        return self.is_admin_level or self.role == UserRole.MODERATOR

    def soft_delete_and_anonymize(self) -> None:
        """GDPR-style deletion: drop personal data, keep immutable ledgers intact."""
        suffix = str(self.id)[:8]
        self.email = f"deleted-{suffix}@anonymized.local"
        self.full_name = "Deleted User"
        self.phone = ""
        self.avatar = ""
        self.status = UserStatus.DELETED
        self.is_active = False
        self.deleted_at = timezone.now()
        self.set_unusable_password()
        self.save(update_fields=[
            "email", "full_name", "phone", "avatar", "status", "is_active",
            "deleted_at", "updated_at", "password",
        ])


class SuspendedUser(User):
    """Proxy so admins can quickly filter suspended accounts."""

    class Meta:
        proxy = True
        verbose_name = "Suspended user"


class DeviceSession(models.Model):
    """Tracks issued refresh tokens per device to support logout-all / session review."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="device_sessions")
    jti = models.CharField(max_length=64, unique=True)
    device_name = models.CharField(max_length=120, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.user.email} · {self.device_name or self.jti[:8]}"


class PhoneOTP(models.Model):
    """Hashed one-time codes for mobile verification / OTP login.

    The raw code never touches the database; delivery goes through an SMS
    provider adapter selected by settings.SMS_PROVIDER.
    """

    class Purpose(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        VERIFY_PHONE = "VERIFY_PHONE", "Verify phone"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"OTP<{self.phone}·{self.purpose}>"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None
