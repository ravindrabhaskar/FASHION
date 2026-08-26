from django.contrib import admin

from marketplace.models import (
    Product,
    ProductImage,
    ProductVariant,
    QuoteOffer,
    QuoteRequest,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "seller_user", "category", "price_inr", "stock",
                    "is_active", "is_customizable")
    list_filter = ("is_active", "category", "ready_to_ship")
    search_fields = ("title", "seller_user__email")
    inlines = (ProductImageInline, ProductVariantInline)
