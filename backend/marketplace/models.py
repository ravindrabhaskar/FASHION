"""Marketplace models: catalog, variants, customize-this-look quotations (PRD §24–28)."""
from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Product(TimeStampedUUIDModel):
    class Category(models.TextChoices):
        WESTERN = "western", "Western"
        ETHNIC = "ethnic", "Ethnic & Traditional"
        FUSION = "fusion", "Fusion"
        FOOTWEAR = "footwear", "Footwear"
        ACCESSORIES = "accessories", "Accessories"
        CUSTOM = "custom", "Made-to-Measure"

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=16, choices=Category.choices)
    price_inr = models.PositiveIntegerField()
    sale_price_inr = models.PositiveIntegerField(null=True, blank=True)

    seller_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    designer = models.ForeignKey(
        "designers.DesignerProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="products",
    )
    brand = models.ForeignKey(
        "brands.BrandProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="products",
    )

    city = models.CharField(max_length=80, blank=True, default="")  # local discovery
    fabric = models.CharField(max_length=60, blank=True, default="")
    colors = models.JSONField(default=list, blank=True)             # ["emerald-green", ...]
    tags = models.JSONField(default=list, blank=True)               # search keywords

    is_customizable = models.BooleanField(default=False)  # accepts quote requests
    ready_to_ship = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    # Semantic search embedding (pgvector in prod; JSON floats elsewhere)
    embedding = models.JSONField(default=list, blank=True)
    embedding_model = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} (₹{self.price_inr})"


class ProductImage(TimeStampedUUIDModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    MEDIA_DOMAIN = "products"
    image = models.ImageField(upload_to="products/", max_length=500)
    alt = models.CharField(max_length=160, blank=True, default="")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]


class ProductVariant(TimeStampedUUIDModel):
    """e.g. name='Size', value='M', or name='Colour', value='Ivory'."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=40)
    value = models.CharField(max_length=60)
    price_delta_inr = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "name", "value"], name="uniq_variant")
        ]


class QuoteRequest(TimeStampedUUIDModel):
    """Customize-this-look: customer brief → designer quotation lifecycle."""

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        RESPONDED = "RESPONDED", "Responded"
        ACCEPTED = "ACCEPTED", "Accepted"       # an offer accepted → becomes Order
        DECLINED = "DECLINED", "Declined by customer"
        CANCELLED = "CANCELLED", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quote_requests"
    )
    designer = models.ForeignKey(
        "designers.DesignerProfile", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="quote_requests",
    )
    product = models.ForeignKey(Product, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="quote_requests")
    design_ref = models.ForeignKey(
        "fashion.GeneratedOutfit", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    brief = models.TextField(max_length=2000)
    budget_inr = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["customer", "-created_at"])]


class QuoteOffer(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        SUPERSEDED = "SUPERSEDED", "Superseded"

    request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="offers")
    price_inr = models.PositiveIntegerField()
    timeline_days = models.PositiveSmallIntegerField(default=14)
    notes = models.TextField(max_length=1000, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROPOSED)
