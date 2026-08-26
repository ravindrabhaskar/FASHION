from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import DeviceSession, PhoneOTP, User, UserRole


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"  # noqa: DJ007

    def clean_role(self):
        role = self.cleaned_data["role"]
        if self.instance.pk and self.instance.is_superuser and role != UserRole.SUPER_ADMIN:
            raise forms.ValidationError("Superusers must keep the SUPER_ADMIN role.")
        return role


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "role", "status", "created_at")
    list_filter = ("role", "status")
    search_fields = ("email", "full_name", "phone")
    readonly_fields = ("id", "last_login", "created_at", "updated_at", "deleted_at")
    form = UserRoleForm
    fieldsets = (
        (None, {"fields": ("id", "email", "full_name", "phone")}),
        ("Platform", {"fields": ("role", "status", "avatar", "onboarding_completed_at")}),
        ("Django", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions",
                               "last_login", "password", "created_at", "updated_at", "deleted_at")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "full_name", "password1", "password2", "role")}),)

    actions = ("suspend_users", "activate_users")

    def suspend_users(self, request, queryset):
        from core.models import record_audit

        for user in queryset.exclude(is_superuser=True):
            before = user.status
            user.status = "SUSPENDED"
            user.save(update_fields=["status", "updated_at"])
            record_audit(actor=request.user, action="user.suspended", target=user,
                         before={"status": before}, after={"status": user.status})

    suspend_users.short_description = "Suspend selected users"

    def activate_users(self, request, queryset):
        from core.models import record_audit

        for user in queryset:
            before = user.status
            user.status = "ACTIVE"
            user.save(update_fields=["status", "updated_at"])
            record_audit(actor=request.user, action="user.activated", target=user,
                         before={"status": before}, after={"status": user.status})

    activate_users.short_description = "Reactivate selected users"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "ip_address", "created_at", "revoked_at")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in DeviceSession._meta.fields]


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "purpose", "created_at", "expires_at", "attempts", "consumed_at")
    readonly_fields = [f.name for f in PhoneOTP._meta.fields]

    def has_add_permission(self, request):
        return False
