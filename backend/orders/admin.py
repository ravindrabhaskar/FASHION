from django.contrib import admin

from orders.models import Order, OrderEvent


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "note", "created_by", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("title_snapshot", "customer", "seller_user", "amount_inr",
                    "status", "created_at")
    list_filter = ("status",)
    search_fields = ("customer__email", "seller_user__email", "title_snapshot")
    inlines = (OrderEventInline,)
    actions = ("mark_shipped",)

    @admin.action(description="Mark selected orders shipped")
    def mark_shipped(self, request, queryset):
        from orders.services import OrderService

        for order in queryset:
            try:
                OrderService.transition(order, to_status=Order.Status.SHIPPED,
                                        actor=None, note="Admin action")
            except Exception:
                continue
