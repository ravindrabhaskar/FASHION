from django.contrib import admin

from creators.models import CreatorProfile, PortfolioItem


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ("handle", "user", "niche", "audience_size", "is_eligible")
    search_fields = ("handle", "user__email")
    readonly_fields = ("stats",)


admin.site.register(PortfolioItem)
