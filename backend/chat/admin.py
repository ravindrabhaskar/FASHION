from django.contrib import admin

from chat.models import Message, Thread


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "is_flagged", "flag_reason", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("subject", "buyer", "seller_user", "updated_at", "archived")
    search_fields = ("buyer__email", "seller_user__email")
    inlines = (MessageInline,)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("body", "thread", "sender", "is_flagged", "created_at")
    list_filter = ("is_flagged",)
    search_fields = ("body",)
