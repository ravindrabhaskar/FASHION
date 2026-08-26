from django.contrib import admin

from profiles.models import StyleProfile, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "gender", "created_at")
    search_fields = ("user__email", "display_name", "city")


@admin.register(StyleProfile)
class StyleProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "completion_cache", "fit_preference", "budget_min", "budget_max")
    search_fields = ("user__email",)
