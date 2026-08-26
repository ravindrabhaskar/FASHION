from django.contrib import admin

from fashionxp.models import (
    Badge,
    Challenge,
    ChallengeEntry,
    FashionXPTransaction,
    Redemption,
    Reward,
    UserBadge,
)


@admin.register(FashionXPTransaction)
class FashionXPTransactionAdmin(admin.ModelAdmin):
    """Ledger rows are immutable — read-only by design (PRD §18)."""

    list_display = ("user", "amount", "reason", "balance_after", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in FashionXPTransaction._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "icon", "xp_bonus", "is_active")
    search_fields = ("code", "name")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")
    search_fields = ("user__email",)


class ChallengeEntryInline(admin.TabularInline):
    model = ChallengeEntry
    extra = 0
    readonly_fields = ("user", "post", "score", "qualified", "ranked_at")


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "starts_at", "ends_at", "xp_reward")
    inlines = (ChallengeEntryInline,)
    actions = ("rescore",)

    @admin.action(description="Re-score all entries (quality-weighted)")
    def rescore(self, request, queryset):
        from fashionxp.services import rescore_entry

        count = 0
        for challenge in queryset:
            for entry in challenge.entries.all():
                rescore_entry(entry)
                count += 1
        self.message_user(request, f"Re-scored {count} entries.")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "cost_xp", "stock", "is_active")
    list_editable = ("is_active",)


@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = ("reward", "user", "cost_xp", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email",)
