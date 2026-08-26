from django.contrib import admin

from designers.models import DesignerProfile, PortfolioImage


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 0


@admin.register(DesignerProfile)
class DesignerProfileAdmin(admin.ModelAdmin):
    list_display = ("studio_name", "slug", "city", "verified", "is_accepting_custom_requests")
    list_filter = ("verified", "is_accepting_custom_requests")
    search_fields = ("studio_name", "user__email", "city")
    actions = ("verify", "unverify")

    @admin.action(description="Mark verified")
    def verify(self, request, queryset):
        from django.utils import timezone

        queryset.update(verified=True, verified_at=timezone.now())

    @admin.action(description="Unmark verified")
    def unverify(self, request, queryset):
        queryset.update(verified=False, verified_at=None)
