from django.contrib import admin

from fashion.models import AIConversation, AIMessage, GeneratedOutfit, Occasion


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "formality", "is_active")
    list_editable = ("is_active",)
    search_fields = ("label", "slug")


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ("role", "content", "changes", "design_version", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "occasion", "message_count", "updated_at", "archived")
    search_fields = ("user__email", "title")
    list_filter = ("archived",)
    inlines = (AIMessageInline,)

    def message_count(self, obj):
        return obj.messages.count()


@admin.register(GeneratedOutfit)
class GeneratedOutfitAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "source", "status", "saved", "created_at")
    list_filter = ("source", "status", "saved")
    search_fields = ("user__email", "title")
    readonly_fields = ("recommendation", "design_state")
