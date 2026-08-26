"""Brands API: storefront registration + discovery."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from brands.models import BrandProfile
from core.exceptions import AppError
from marketplace.models import Product


def brand_payload(brand: BrandProfile, *, detailed: bool = False) -> dict:
    data = {
        "id": str(brand.id),
        "slug": brand.slug,
        "name": brand.name,
        "city": brand.city,
        "categories": brand.categories,
        "verified": brand.verified,
        "product_count": Product.objects.filter(brand=brand, is_active=True).count(),
    }
    if detailed:
        data.update({"about": brand.about, "website": brand.website})
    return data


class BrandsListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        brands = BrandProfile.objects.all()
        city = request.query_params.get("city", "")
        if city:
            brands = brands.filter(city__iexact=city)
        return Response({
            "count": brands.count(),
            "results": [brand_payload(b) for b in brands[:50]],
        })


class MyBrandView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        brand = getattr(request.user, "brand_profile", None)
        if not brand:
            raise AppError("You don't have a brand profile yet.", code="no_brand_profile")
        return Response(brand_payload(brand, detailed=True))

    def post(self, request):
        if getattr(request.user, "role", "") not in ("BRAND", "ADMIN", "SUPER_ADMIN"):
            raise AppError(
                "Switch your account role to BRAND first (contact support).",
                code="role_required",
            )
        payload = request.data or {}
        slug = str(payload.get("slug", "")).strip().lower().replace(" ", "-")
        if not slug:
            raise AppError("A storefront link is required.", code="validation_error")
        if BrandProfile.objects.filter(slug=slug).exclude(user=request.user).exists():
            raise AppError("That storefront link is taken.", code="slug_taken")
        brand, _ = BrandProfile.objects.update_or_create(
            user=request.user,
            defaults={
                "slug": slug[:50],
                "name": str(payload.get("name", ""))[:120],
                "about": str(payload.get("about", "")),
                "website": str(payload.get("website", "")),
                "city": str(payload.get("city", ""))[:80],
                "categories": [str(c).lower() for c in (payload.get("categories") or [])][:10],
            },
        )
        return Response(brand_payload(brand), status=status.HTTP_201_CREATED)


class BrandDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, slug: str):
        brand = get_object_or_404(BrandProfile, slug=slug)
        payload = brand_payload(brand, detailed=True)
        products = Product.objects.filter(brand=brand, is_active=True)[:12]
        from designers.services import product_image_url

        payload["products"] = [
            {
                "id": str(p.id), "title": p.title, "price_inr": p.price_inr,
                "category": p.category, "image": product_image_url(p),
            }
            for p in products
        ]
        return Response(payload)
