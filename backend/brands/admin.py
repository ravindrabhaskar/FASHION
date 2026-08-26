from django.contrib import admin

from brands.models import BrandProfile


@admin.register(BrandProfile)
class BrandProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "verified")
    search_fields = ("name", "user__email")
