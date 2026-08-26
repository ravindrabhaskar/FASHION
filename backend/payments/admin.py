from django.contrib import admin

from payments.models import Payment, PaymentMethodRecord, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "amount_inr", "status", "created_at")
    list_filter = ("provider", "status")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "event_type", "ok", "processed_at")
    readonly_fields = [f.name for f in WebhookEvent._meta.fields]


admin.site.register(PaymentMethodRecord)
