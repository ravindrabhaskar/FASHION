from django.contrib import admin

from social.models import (
    Comment,
    Follow,
    Like,
    Post,
    PostItemTag,
    Report,
    SavedPost,
)


class PostItemTagInline(admin.TabularInline):
    model = PostItemTag
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("caption", "user", "occasion", "status", "like_count",
                    "comment_count", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "caption")
    readonly_fields = ("ai_metadata", "like_count", "comment_count")
    inlines = (PostItemTagInline,)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("text", "post", "user", "is_hidden", "created_at")
    search_fields = ("text", "user__email")


admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(SavedPost)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("target_type", "target_id", "reason", "status", "reporter", "created_at")
    list_filter = ("status", "reason", "target_type")
