"""Wardrobe API: items CRUD, wear tracking, closet styling, daily assistant."""
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from analytics.services import record_event
from core.exceptions import AppError
from fashion.registry import get_occasion
from wardrobe.models import WardrobeItem
from wardrobe.services import WardrobeService

MAX_PHOTO_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _validate_image_upload(file) -> bytes:
    if not isinstance(file, UploadedFile):
        raise AppError("A photo file is required.", code="photo_required")
    if getattr(file, "size", 0) > MAX_PHOTO_BYTES:
        raise AppError("Photo must be under 10 MB.", code="photo_too_large")
    content_type = (getattr(file, "content_type", "") or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise AppError("Only JPEG, PNG or WebP photos are supported.", code="unsupported_media")
    header = file.read(16)
    file.seek(0)
    sigs = (b"\xff\xd8\xff", b"\x89PNG", b"RIFF")  # JPEG, PNG, WEBP(RIFF)
    if not any(header.startswith(sig) for sig in sigs):
        raise AppError("That file doesn't look like a valid image.", code="invalid_image")
    return file.read()


def _image_url(item: WardrobeItem) -> str:
    if not item.image:
        return ""
    url = item.image.url if hasattr(item.image, "url") else str(item.image)
    if url.startswith("/"):
        from django.conf import settings as dj_settings

        url = f"http://localhost:8000{url}" if dj_settings.DEBUG else url
    return url


def _item_payload(item: WardrobeItem, *, brief: bool = False) -> dict:
    data = {
        "id": str(item.id),
        "name": item.name,
        "category": item.category,
        "category_label": item.get_category_display(),
        "status": item.status,
        "color_primary": item.color_primary,
        "color_hex": item.color_hex,
        "favorite": item.favorite,
        "times_worn": item.times_worn,
        "last_worn_at": item.last_worn_at,
        "image": _image_url(item),
        "created_at": item.created_at,
    }
    if brief:
        return data
    data.update({
        "fabric": item.fabric,
        "pattern": item.pattern,
        "formality": item.formality,
        "seasons": item.seasons,
        "occasion_slugs": item.occasion_slugs,
        "style_tags": item.style_tags,
        "notes": item.notes,
    })
    return data


class WardrobeItemListView(APIView):
    """GET list (filters: category, favorite) · POST add item with photo → AI attributes."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        items = WardrobeItem.objects.filter(user=request.user, archived=False)
        category = request.query_params.get("category", "")
        if category:
            if category not in WardrobeItem.Category.values:
                raise AppError("Unknown wardrobe category.", code="invalid_category")
            items = items.filter(category=category)
        if request.query_params.get("favorite") == "true":
            items = items.filter(favorite=True)

        limit = min(int(request.query_params.get("limit", "100") or 100), 200)
        results = [_item_payload(i) for i in items[:limit]]
        return Response({"count": items.count(), "results": results})

    def post(self, request):
        photo = request.FILES.get("photo")
        image_bytes = _validate_image_upload(photo)

        category = (request.data.get("category", "") or "").strip()
        if category and category not in WardrobeItem.Category.values:
            raise AppError("Unknown wardrobe category.", code="invalid_category")

        item = WardrobeService.add_item(
            request.user,
            image_bytes=image_bytes,
            filename=getattr(photo, "name", "") or "item.jpg",
            category=category,
            notes=str(request.data.get("notes", "") or ""),
        )
        return Response(_item_payload(item), status=status.HTTP_201_CREATED)


class WardrobeItemDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, item_id):
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        return Response(_item_payload(item))

    def patch(self, request, item_id):
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        payload = request.data or {}

        if "name" in payload:
            name = str(payload["name"] or "").strip()[:120]
            if not name:
                raise AppError("Give this piece a name.", code="empty_name")
            item.name = name
        if "category" in payload:
            category = str(payload["category"] or "")
            if category not in WardrobeItem.Category.values:
                raise AppError("Unknown wardrobe category.", code="invalid_category")
            item.category = category
        if "favorite" in payload:
            item.favorite = payload["favorite"] in (True, "true", "True", 1, "1")
        if "archived" in payload:
            item.archived = payload["archived"] in (True, "true", "True", 1, "1")
        if "notes" in payload:
            item.notes = str(payload["notes"] or "")[:300]

        item.save()
        record_event(user=request.user, name="wardrobe_item_updated",
                     properties={"item_id": str(item.id)})
        return Response(_item_payload(item))

    def delete(self, request, item_id):
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WardrobeItemWornView(APIView):
    """POST — log that the user wore this piece today."""

    permission_classes = [IsAuthenticatedActive]

    def post(self, request, item_id):
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        item = WardrobeService.mark_worn(item)
        return Response(_item_payload(item))


class ClosetRecommendView(APIView):
    """POST {occasion?, budget_inr?} — style a full look from the user's own closet."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        payload = request.data or {}
        occasion = payload.get("occasion") or None
        if occasion and not get_occasion(occasion):
            raise AppError("Unknown occasion.", code="unknown_occasion")

        budget_raw = payload.get("budget_inr")
        budget_inr = None
        if budget_raw not in (None, "", "null"):
            try:
                budget_inr = max(0, min(int(budget_raw), 1_000_000))
            except (TypeError, ValueError) as exc:
                raise AppError("Budget must be a number of rupees.", code="invalid_budget") from exc

        outfit, used_items = WardrobeService.recommend_from_closet(
            request.user, occasion=occasion, budget_inr=budget_inr
        )
        from fashion.views import _outfit_payload

        return Response({
            "outfit": _outfit_payload(outfit),
            "items": [_item_payload(i, brief=True) for i in used_items],
        }, status=status.HTTP_201_CREATED)


class DailySuggestionView(APIView):
    """GET ?city= — weather-aware 'what should I wear today' suggestion."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        city = request.query_params.get("city", "") or ""
        data = WardrobeService.build_daily_suggestion(request.user, city_override=city)
        # Fill brief item images now that we have request context.
        closet = data.get("closet_outfit")
        if closet:
            ids = {i["id"] for i in closet["items"]}
            items = WardrobeItem.objects.filter(id__in=ids, user=request.user)
            by_id = {str(i.id): i for i in items}
            for brief_item in closet["items"]:
                model_item = by_id.get(brief_item["id"])
                brief_item["image"] = _image_url(model_item) if model_item else ""
        return Response(data)
