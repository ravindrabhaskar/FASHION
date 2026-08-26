"""Designer domain services."""
from django.utils import timezone

from analytics.services import record_event
from core.exceptions import AppError
from designers.models import DesignerProfile


class DesignerService:
    @staticmethod
    def register(user, *, studio_name: str, slug: str, city: str = "",
                 tagline: str = "", bio: str = "", specialities: list | None = None,
                 experience_years=None) -> DesignerProfile:
        if getattr(user, "role", "") not in ("DESIGNER", "ADMIN", "SUPER_ADMIN"):
            raise AppError(
                "Switch your account role to DESIGNER first (contact support).",
                code="role_required",
            )
        if DesignerProfile.objects.filter(slug=slug).exists():
            raise AppError("That storefront link is taken.", code="slug_taken")
        profile, _ = DesignerProfile.objects.update_or_create(
            user=user,
            defaults={
                "studio_name": studio_name[:120],
                "slug": slug[:50],
                "city": city[:80],
                "tagline": tagline[:160],
                "bio": bio,
                "specialities": [s.strip().lower() for s in (specialities or [])][:10],
                "experience_years": experience_years,
            },
        )
        record_event(user=user, name="designer_registered",
                     properties={"designer_id": str(profile.id)})
        return profile

    @staticmethod
    def verify(profile: DesignerProfile, *, verified: bool) -> DesignerProfile:
        profile.verified = verified
        profile.verified_at = timezone.now() if verified else None
        profile.save(update_fields=["verified", "verified_at", "updated_at"])
        return profile


def designer_payload(profile: DesignerProfile, *, detailed: bool = False) -> dict:
    from marketplace.models import Product

    products = Product.objects.filter(designer=profile, is_active=True)[:12 if detailed else 4]
    data = {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "slug": profile.slug,
        "studio_name": profile.studio_name,
        "tagline": profile.tagline,
        "city": profile.city,
        "specialities": profile.specialities,
        "verified": profile.verified,
        "is_accepting_custom_requests": profile.is_accepting_custom_requests,
        "product_count": Product.objects.filter(designer=profile, is_active=True).count(),
    }
    if detailed:
        data.update({
            "bio": profile.bio,
            "experience_years": profile.experience_years,
            "instagram": profile.instagram,
            "products": [
                {
                    "id": str(p.id), "title": p.title, "price_inr": p.price_inr,
                    "category": p.category, "image": product_image_url(p),
                    "is_customizable": p.is_customizable,
                }
                for p in products
            ],
        })
    return data


def product_image_url(product) -> str:
    first = product.images.first()
    if not first:
        return ""
    url = first.image.url if hasattr(first.image, "url") else str(first.image)
    if url.startswith("/"):
        from django.conf import settings as dj_settings

        url = f"http://localhost:8000{url}" if dj_settings.DEBUG else url
    return url
