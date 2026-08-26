"""Stylist + designer domain services. Views stay thin; logic lives here."""
from django.utils import timezone

from ai import orchestrator
from ai.schemas import DesignState, RecommendationResult
from analytics.services import record_event
from fashion.models import AIConversation, AIMessage, GeneratedOutfit


def _style_context(user) -> dict:
    sp = getattr(user, "style_profile", None)
    if not sp:
        return {}
    return {
        "preferred_styles": sp.preferred_styles,
        "favorite_colors": sp.favorite_colors,
        "avoided_colors": sp.avoided_colors,
        "fit_preference": sp.fit_preference,
        "budget_range": [sp.budget_min, sp.budget_max],
        "traditional_modern_balance": sp.traditional_modern_balance,
        "common_occasions": sp.common_occasions,
    }


class StylistService:
    @staticmethod
    def analyze_photo(user, *, image_bytes: bytes, occasion: str | None, user_notes: str = ""):
        orchestrator.enforce_quota(user=user, scope="ai_text")
        analysis = orchestrator.analyze_image(
            user=user, image_bytes=image_bytes, occasion=occasion, user_notes=user_notes
        )
        record_event(user=user, name="styling_started",
                     properties={"occasion": occasion or "", "has_notes": bool(user_notes)})
        return analysis

    @staticmethod
    def recommend(user, *, analysis=None, occasion: str | None = None,
                  budget_inr: int | None = None, user_notes: str = "",
                  persist: bool = True) -> GeneratedOutfit:
        orchestrator.enforce_quota(user=user, scope="ai_text")
        result: RecommendationResult = orchestrator.recommend_outfit(
            user=user, analysis=analysis, occasion=occasion, budget_inr=budget_inr,
            user_notes=user_notes, style_context=_style_context(user),
        )
        outfit = None
        if persist:
            outfit = GeneratedOutfit.objects.create(
                user=user,
                source=GeneratedOutfit.Source.STYLIST,
                status=GeneratedOutfit.Status.COMPLETED,
                title=result.headline[:140],
                occasion=occasion or "",
                budget_inr=budget_inr,
                recommendation=result.model_dump(),
            )
            record_event(user=user, name="styling_completed", properties={
                "occasion": occasion or "", "budget_inr": budget_inr,
                "outfit_id": str(outfit.id), "confidence": result.confidence,
            })
        return result if not persist else outfit

    @staticmethod
    def request_image_job(outfit: GeneratedOutfit) -> GeneratedOutfit:
        """Queue an async image render for a look (idempotent while in-flight)."""
        from fashion.tasks import render_outfit_image

        if outfit.status == GeneratedOutfit.Status.GENERATING and \
                (timezone.now() - outfit.updated_at).total_seconds() < 300:
            return outfit  # already rendering
        outfit.status = GeneratedOutfit.Status.QUEUED
        outfit.save(update_fields=["status", "updated_at"])
        transaction = render_outfit_image.delay(str(outfit.id))
        outfit.image_prompt = outfit.image_prompt or _image_prompt_for(outfit)
        outfit.save(update_fields=["image_prompt"])
        record_event(user=outfit.user, name="outfit_generation_queued",
                     properties={"outfit_id": str(outfit.id), "task_id": transaction.id})
        return outfit


def _image_prompt_for(outfit: GeneratedOutfit) -> str:
    rec = outfit.recommendation or {}
    headline = rec.get("headline") or outfit.title or "fashion look"
    components = ", ".join(
        c.get("item", {}).get("description", "") for c in rec.get("outfit_components", [])
    ) or ""
    return f"Fashion concept illustration: {headline}. {components} Editorial studio photography."


class DesignerService:
    MAX_MESSAGES_PER_CONVERSATION = 60

    @staticmethod
    def create_conversation(user, *, occasion: str | None = None, budget_inr: int | None = None,
                            opening_request: str | None = None) -> AIConversation:
        conversation = AIConversation.objects.create(
            user=user, occasion=occasion or "", budget_inr=budget_inr,
        )
        if opening_request:
            DesignerService.send_message(conversation, message=opening_request)
        return conversation

    @staticmethod
    def send_message(conversation: AIConversation, *, message: str) -> AIMessage:
        orchestrator.enforce_quota(user=conversation.user, scope="ai_text")

        count = conversation.messages.count()
        if count >= DesignerService.MAX_MESSAGES_PER_CONVERSATION:
            from core.exceptions import AppError

            raise AppError("This design session is full. Start a new design to continue.",
                           code="conversation_full")

        AIMessage.objects.create(conversation=conversation, role=AIMessage.Role.USER, content=message)

        turn = orchestrator.designer_turn(
            user=conversation.user,
            conversation_history=[
                {"role": m.role.lower(), "content": m.content}
                for m in conversation.messages.all()[:count]  # history BEFORE this turn's reply
            ],
            message=message,
            current_design=conversation.get_design_state(),
        )

        new_version = count + 1
        assistant = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.ASSISTANT,
            content=turn.reply,
            changes=turn.changes,
            design_version=new_version,
        )

        # Persist evolved state — only the fields the model changed mutate.
        conversation.design_state = turn.updated_design.model_dump()
        if not conversation.title:
            conversation.title = message[:80]
        conversation.save()

        record_event(user=conversation.user, name="designer_turn_completed",
                     properties={"conversation_id": str(conversation.id),
                                 "changes": len(turn.changes), "version": new_version})
        from fashionxp.services import award

        award(conversation.user, "designer_turn", ref_type="conversation",
              ref_id=str(conversation.id))
        return assistant

    @staticmethod
    def materialize_look(conversation: AIConversation) -> GeneratedOutfit:
        """Snapshot the current design as a concrete look (with image job)."""
        design = conversation.get_design_state() or DesignState()
        outfit = GeneratedOutfit.objects.create(
            user=conversation.user,
            source=GeneratedOutfit.Source.DESIGNER,
            status=GeneratedOutfit.Status.QUEUED,
            title=f"{design.garment_type.replace('-', ' ').title()} · {design.base_color.title()}",
            occasion=conversation.occasion,
            budget_inr=design.target_budget_inr or conversation.budget_inr,
            design_state=design.model_dump(),
            conversation=conversation,
            version=conversation.messages.count(),
        )
        from fashion.tasks import render_outfit_image

        render_outfit_image.delay(str(outfit.id))
        record_event(user=conversation.user, name="outfit_generated",
                     properties={"outfit_id": str(outfit.id), "source": "designer"})
        return outfit
