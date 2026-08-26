from django.contrib import admin

from ai.models import AIUsageLog


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = (
        "feature", "user", "provider", "status", "latency_ms",
        "estimated_cost_usd", "cache_hit", "created_at",
    )
    list_filter = ("feature", "provider", "status", "cache_hit")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in AIUsageLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
