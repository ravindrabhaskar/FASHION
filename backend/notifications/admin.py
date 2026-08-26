from django.contrib import admin

from notifications.models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "read_at", "created_at")
    list_filter = ("type",)
    search_fields = ("user__email", "title")
    readonly_fields = ("data",)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "platform", "is_active", "created_at")
    list_filter = ("platform", "is_active")
