from django.contrib import admin

from campaigns.models import Application, Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "brand_user", "status", "budget_inr", "min_audience")
    list_filter = ("status",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "creator", "status", "created_at")
    list_filter = ("status",)
