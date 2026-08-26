from django.contrib import admin

from subscriptions.models import SubscriptionPlan, UserSubscription
from subscriptions.services import get_entitlements


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "tier", "price_inr", "ai_text_daily_limit",
                    "ai_image_monthly_limit", "max_saved_looks", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name", "code")
    fieldsets = (
        ("Identity", {"fields": ("code", "name", "tier", "price_inr", "billing_interval_days", "is_active")}),
        ("Entitlements", {"fields": ("ai_text_daily_limit", "ai_image_monthly_limit",
                                     "max_saved_looks", "wardrobe_item_limit",
                                     "designer_chat_enabled", "customization_requests_enabled")}),
        ("Presentation", {"fields": ("features",)}),
    )

    def save_model(self, request, obj, form, change):
        from core.models import record_audit

        before = None
        if change:
            old = type(obj).objects.get(pk=obj.pk)
            before = {f: getattr(old, f) for f in form.changed_data}
        super().save_model(request, obj, form, change)
        record_audit(actor=request.user, action="plan.updated" if change else "plan.created",
                     target=obj, before=before,
                     after={f: getattr(obj, f) for f in (form.changed_data or [])})


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_start", "current_period_end")
    list_filter = ("status",)
    search_fields = ("user__email",)
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        from core.models import record_audit

        super().save_model(request, obj, form, change)
        record_audit(actor=request.user, action="subscription.admin_updated", target=obj)


# Expose entitlement snapshot for support staff via a read-only view on user pages
def entitlements_preview(user):
    ent = get_entitlements(user)
    return f"{ent.tier or 'FREE'} · text {ent.ai_text_daily_limit}/day · images {ent.ai_image_monthly_limit}/mo"
