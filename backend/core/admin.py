from django.contrib import admin
from django.utils.html import format_html

from core.models import AuditLog, FeatureFlag, SystemConfig
from core.services import set_config


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value_preview", "updated_at", "updated_by")
    search_fields = ("key", "description")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Value")
    def value_preview(self, obj):
        text = str(obj.value)
        return text if len(text) <= 80 else text[:77] + "..."

    def save_model(self, request, obj, form, change):
        from core.models import record_audit

        before = None
        if change:
            old = type(obj).objects.get(pk=obj.pk)
            before = {"value": old.value}
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        record_audit(
            actor=request.user,
            action="config.changed" if change else "config.created",
            target=obj,
            before=before,
            after={"value": obj.value},
        )
        set_config(obj.key, obj.value, updated_by=request.user)


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ("key", "enabled_badge", "description", "updated_at")
    list_editable = ()  # edits go through save_model for auditing
    search_fields = ("key", "description")
    actions = ("enable_flags", "disable_flags")

    @admin.display(boolean=True, description="Enabled")
    def enabled_badge(self, obj):
        return obj.enabled

    def _set_enabled(self, request, queryset, enabled: bool):
        from core.models import record_audit

        for flag in queryset:
            before = flag.enabled
            flag.enabled = enabled
            flag.save(update_fields=["enabled", "updated_at"])
            record_audit(actor=request.user, action="flag.toggled", target=flag,
                         before={"enabled": before}, after={"enabled": enabled})

    @admin.action(description="Enable selected flags")
    def enable_flags(self, request, queryset):
        self._set_enabled(request, queryset, True)

    @admin.action(description="Disable selected flags")
    def disable_flags(self, request, queryset):
        self._set_enabled(request, queryset, False)

    def save_model(self, request, obj, form, change):
        from core.models import record_audit

        before = {"enabled": type(obj).objects.get(pk=obj.pk).enabled} if change else None
        super().save_model(request, obj, form, change)
        record_audit(actor=request.user, action="flag.updated" if change else "flag.created",
                     target=obj, before=before, after={"enabled": obj.enabled})


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "target_type", "target_id", "actor", "created_at")
    list_filter = ("action", "target_type")
    search_fields = ("target_id", "actor__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Detail")
    def audit_summary(self, obj):  # pragma: no cover - display helper
        return format_html("<code>{}</code>", (obj.after or obj.before or {}))
