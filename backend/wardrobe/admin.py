from django.contrib import admin

from wardrobe.models import WardrobeItem


@admin.register(WardrobeItem)
class WardrobeItemAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "status", "favorite", "times_worn", "created_at")
    list_filter = ("category", "status", "favorite")
    search_fields = ("user__email", "name")
    readonly_fields = ("attributes",)
