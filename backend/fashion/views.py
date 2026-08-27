"""Fashion API: occasions, stylist flow, outfit generation, conversational designer."""
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from ai import orchestrator
from analytics.services import record_event
from core.exceptions import AppError
from core.services import is_enabled
from fashion.models import AIConversation, GeneratedOutfit, Occasion
from fashion.registry import get_occasion
from fashion.services import DesignerService, StylistService

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


class OccasionsView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        data = [
            {
                "slug": o.slug,
                "label": o.label,
                "description": o.description,
                "formality": o.formality,
            }
            for o in Occasion.objects.filter(is_active=True)
        ]
        return Response(data)


class AnalyzePhotoView(APIView):
    """POST /fashion/analyze — multipart photo + occasion → structured analysis."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        photo = request.FILES.get("photo")
        image_bytes = _validate_image_upload(photo)
        occasion = request.data.get("occasion", "") or None
        user_notes = (request.data.get("notes", "") or "")[:500]
        if occasion and not get_occasion(occasion):
            raise AppError("Unknown occasion.", code="unknown_occasion")

        analysis = StylistService.analyze_photo(
            request.user, image_bytes=image_bytes, occasion=occasion, user_notes=user_notes
        )
        return Response({
            "analysis_id": None,  # stateless v1; analysis echoed back for /recommend
            "analysis": analysis.model_dump(),
        })


class RecommendOutfitView(APIView):
    """POST /fashion/recommend — JSON {occasion, budget_inr, notes, analysis?} → look."""

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

        user_notes = str(payload.get("notes", ""))[:500]

        analysis = None
        raw_analysis = payload.get("analysis")
        if isinstance(raw_analysis, dict):
            from ai.schemas import ImageAnalysis

            try:
                analysis = ImageAnalysis.model_validate(raw_analysis)
            except Exception:
                analysis = None  # client-provided analysis is advisory only

        outfit = StylistService.recommend(
            request.user, analysis=analysis, occasion=occasion,
            budget_inr=budget_inr, user_notes=user_notes,
        )
        return Response(_outfit_payload(outfit), status=status.HTTP_201_CREATED)


class GenerateOutfitView(APIView):
    """POST /outfits/generate — queue an AI concept image for a saved look."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        if not is_enabled("ai_designer", default=True):
            raise AppError("AI designer is coming soon.", code="feature_disabled")

        outfit_id = request.data.get("outfit_id")
        prompt_override = str(request.data.get("prompt", ""))[:800]

        if outfit_id:
            outfit = get_object_or_404(GeneratedOutfit, id=outfit_id, user=request.user)
            if prompt_override:
                outfit.image_prompt = prompt_override
                outfit.save(update_fields=["image_prompt"])
        else:
            # Standalone generation from a design snapshot (designer/customize flows).
            design = request.data.get("design_state") or {}
            from ai.schemas import DesignState

            try:
                design_obj = DesignState.model_validate(design)
            except Exception as exc:
                raise AppError("Invalid design state.", code="invalid_design") from exc
            outfit = GeneratedOutfit.objects.create(
                user=request.user,
                source=GeneratedOutfit.Source.CUSTOMIZE if request.data.get("source_outfit_id")
                else GeneratedOutfit.Source.DESIGNER,
                status=GeneratedOutfit.Status.QUEUED,
                title=f"{design_obj.garment_type.replace('-', ' ').title()} · {design_obj.base_color.title()}",
                design_state=design_obj.model_dump(),
                source_outfit_id=request.data.get("source_outfit_id"),
                image_prompt=prompt_override,
            )

        StylistService.request_image_job(outfit)
        record_event(user=request.user, name="outfit_generated",
                     properties={"outfit_id": str(outfit.id)})
        return Response(_outfit_payload(outfit), status=status.HTTP_202_ACCEPTED)


class OutfitListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        outfits = GeneratedOutfit.objects.filter(user=request.user).order_by("-created_at")
        saved_only = request.query_params.get("saved") == "true"
        if saved_only:
            outfits = outfits.filter(saved=True)

        limit = min(int(request.query_params.get("limit", "20") or 20), 100)
        results = [_outfit_payload(o) for o in outfits[:limit]]
        return Response({"count": outfits.count(), "results": results})


class OutfitDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, outfit_id):
        outfit = get_object_or_404(GeneratedOutfit, id=outfit_id, user=request.user)
        return Response(_outfit_payload(outfit))

    def delete(self, request, outfit_id):
        outfit = get_object_or_404(GeneratedOutfit, id=outfit_id, user=request.user)
        outfit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SaveOutfitView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def post(self, request, outfit_id):
        from subscriptions.services import get_entitlements

        outfit = get_object_or_404(GeneratedOutfit, id=outfit_id, user=request.user)
        ent = get_entitlements(request.user)
        used = GeneratedOutfit.objects.filter(user=request.user, saved=True).count()
        if not outfit.saved and used >= ent.max_saved_looks:
            raise AppError(
                f"You've reached your limit of {ent.max_saved_looks} saved looks. "
                "Upgrade for unlimited boards.",
                code="quota_exceeded",
            )
        outfit.saved = True
        outfit.saved_at = timezone.now()
        outfit.save(update_fields=["saved", "saved_at"])
        record_event(user=request.user, name="outfit_saved",
                     properties={"outfit_id": str(outfit.id)})
        from fashionxp.services import award

        award(request.user, "outfit_saved", ref_type="outfit", ref_id=str(outfit.id))
        return Response(_outfit_payload(outfit))


# ---- Conversational designer -----------------------------------------------

class ConversationListView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        conversations = AIConversation.objects.filter(user=request.user, archived=False)
        return Response([
            {
                "id": str(c.id),
                "title": c.title,
                "occasion": c.occasion,
                "budget_inr": c.budget_inr,
                "message_count": c.messages.count(),
                "updated_at": c.updated_at,
            }
            for c in conversations[:50]
        ])

    def post(self, request):
        payload = request.data or {}
        occasion = payload.get("occasion") or None
        if occasion and not get_occasion(occasion):
            raise AppError("Unknown occasion.", code="unknown_occasion")
        conversation = DesignerService.create_conversation(
            request.user,
            occasion=occasion,
            budget_inr=_safe_int(payload.get("budget_inr")),
            opening_request=str(payload.get("opening_request", ""))[:800] or None,
        )
        return Response(_conversation_detail(conversation), status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticatedActive]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
        return Response(_conversation_detail(conversation))

    def delete(self, request, conversation_id):
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
        conversation.archived = True
        conversation.save(update_fields=["archived", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationMessageView(APIView):
    """POST — send a message to the designer; returns the assistant turn + new state."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request, conversation_id):
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
        message = str((request.data or {}).get("message", "")).strip()
        if not message:
            raise AppError("Tell the designer what you'd like to change.", code="empty_message")
        if len(message) > 800:
            raise AppError("Message too long (max 800 characters).", code="message_too_long")

        assistant_message = DesignerService.send_message(conversation, message=message)
        detail = _conversation_detail(conversation)
        detail["assistant_message_id"] = str(assistant_message.id)
        return Response(detail)


class MaterializeLookView(APIView):
    """POST — snapshot a conversation's current design into a concrete look + image job."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request, conversation_id):
        orchestrator.enforce_quota(user=request.user, scope="ai_image")
        conversation = get_object_or_404(AIConversation, id=conversation_id, user=request.user)
        outfit = DesignerService.materialize_look(conversation)
        return Response(_outfit_payload(outfit), status=status.HTTP_202_ACCEPTED)


class TryOnView(APIView):
    """POST {outfit_id} — virtual try-on concept render (PRD §42; feature-flagged)."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request, outfit_id: str | None = None):
        if not is_enabled("virtual_tryon", default=True):
            raise AppError("Virtual try-on is rolling out soon.", code="feature_disabled")
        orchestrator.enforce_quota(user=request.user, scope="ai_image")
        outfit_id = outfit_id or (request.data or {}).get("outfit_id", "")
        base = get_object_or_404(GeneratedOutfit, id=outfit_id, user=request.user)

        garment = ", ".join(
            c.get("item", {}).get("description", "") for c in
            (base.recommendation or {}).get("outfit_components", [])
        )[:400] or base.title
        prompt = (
            f"Photorealistic virtual try-on preview of this outfit on a neutral studio mannequin: "
            f"{garment}. Full-body, soft lighting, plain backdrop."
        )
        tryon_outfit = GeneratedOutfit.objects.create(
            user=request.user,
            source=GeneratedOutfit.Source.CUSTOMIZE,
            status=GeneratedOutfit.Status.QUEUED,
            title=f"Try-on · {base.title[:120]}",
            occasion=base.occasion,
            recommendation=base.recommendation,
            source_outfit=base,
            image_prompt=prompt,
        )
        StylistService.request_image_job(tryon_outfit)
        tryon_outfit.refresh_from_db()  # eager workers may complete synchronously
        record_event(user=request.user, name="tryon_requested",
                     properties={"outfit_id": str(base.id), "tryon_id": str(tryon_outfit.id)})
        return Response(_outfit_payload(tryon_outfit), status=status.HTTP_202_ACCEPTED)


# ---- helpers -----------------------------------------------------------------

def _safe_int(value):
    try:
        return max(0, int(value)) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _outfit_payload(outfit: GeneratedOutfit) -> dict:
    return {
        "id": str(outfit.id),
        "source": outfit.source,
        "status": outfit.status,
        "title": outfit.title,
        "occasion": outfit.occasion,
        "budget_inr": outfit.budget_inr,
        "recommendation": outfit.recommendation,
        "design_state": outfit.design_state,
        "image": request_image_url(outfit),
        "image_prompt": outfit.image_prompt,
        "version": outfit.version,
        "saved": outfit.saved,
        "failed_reason": outfit.failed_reason,
        "created_at": outfit.created_at,
    }


def request_image_url(outfit) -> str:
    if not outfit.image:
        return ""
    url = outfit.image.url if hasattr(outfit.image, "url") else str(outfit.image)
    if url.startswith("/"):
        from django.conf import settings as dj_settings

        url = f"http://localhost:8000{url}" if dj_settings.DEBUG else url
    return url


def _conversation_detail(conversation: AIConversation) -> dict:
    messages = []
    for m in conversation.messages.all():
        messages.append({
            "id": str(m.id),
            "role": m.role.lower(),
            "content": m.content,
            "changes": m.changes,
            "design_version": m.design_version,
            "created_at": m.created_at,
        })
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "occasion": conversation.occasion,
        "budget_inr": conversation.budget_inr,
        "design_state": conversation.design_state,
        "messages": messages,
        "updated_at": conversation.updated_at,
    }


# ---- Trends + multilingual (Phase 7) ---------------------------------------


class TrendsView(APIView):
    """GET — deterministic fashion trends snapshot (colors, fabrics, categories)."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        from fashion.trends import trend_snapshot

        return Response(trend_snapshot(limit=_safe_int(request.query_params.get("limit")) or 8))


class I18nStringsView(APIView):
    """GET ?lang=xx — localized UI strings for the mobile app (PRD §45)."""

    permission_classes = [IsAuthenticatedActive]

    def get(self, request):
        from fashion.i18n import SUPPORTED_LANGUAGES, strings_for

        locale = str(request.query_params.get("lang", ""))[:8] or "en"
        return Response({
            "locale": locale,
            "supported": SUPPORTED_LANGUAGES,
            "strings": strings_for(locale),
        })
