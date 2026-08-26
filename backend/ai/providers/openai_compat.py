"""OpenAI-compatible provider adapter (also works for many self-hosted/3rd-party gateways).

Configuration via settings: OPENAI_BASE_URL, OPENAI_API_KEY, model names per task.
Implements the same protocol as MockAIProvider; structured outputs are enforced
via JSON responses and validated by the orchestrator.
"""
import base64

from django.conf import settings
from openai import OpenAI

from ai.schemas import (
    DesignState,
    DesignTurnResponse,
    ImageAnalysis,
    RecommendationResult,
)

JSON_SCHEMAS = {
    "image_analysis": ImageAnalysis,
    "recommendation": RecommendationResult,
    "design_turn": DesignTurnResponse,
}


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self):
        self._client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        )

    def _chat_json(self, *, system: str, user_content: str | list, model: str,
                   schema_model: type) -> dict:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        import json

        return json.loads(response.choices[0].message.content or "{}")

    # ---- Vision ---------------------------------------------------------
    def analyze_image(self, *, image_bytes: bytes, occasion: str | None = None,
                      user_notes: str = "") -> ImageAnalysis:
        from ai.prompts import stylist_system_prompt as _  # noqa: F401 (documented pairing)
        from ai.prompts import vision_analysis_prompt

        b64 = base64.b64encode(image_bytes).decode()
        data_url = f"data:image/jpeg;base64,{b64}"
        payload = self._chat_json(
            system="You analyze photos as fashion metadata only. Never identify people or judge bodies.",
            user_content=[
                {"type": "text", "text": vision_analysis_prompt(occasion, user_notes)},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
            model=settings.OPENAI_VISION_MODEL,
            schema_model=ImageAnalysis,
        )
        return ImageAnalysis.model_validate(payload)

    # ---- LLM ------------------------------------------------------------
    def recommend(self, *, analysis: ImageAnalysis | None, occasion: str | None,
                  budget_inr: int | None, user_notes: str = "",
                  style_context: dict | None = None,
                  language: str = "en") -> RecommendationResult:
        from ai.prompts import stylist_system_prompt

        context_lines = []
        if analysis:
            context_lines.append(f"Photo analysis: {analysis.summary}")
            context_lines.append("Detected clothing: "
                                 + "; ".join(g.description or g.category for g in analysis.detected_clothing))
        if style_context:
            import json

            context_lines.append("User style profile: " + json.dumps(style_context))
        if budget_inr:
            context_lines.append(f"Budget: ₹{budget_inr}")
        if user_notes:
            context_lines.append(f"User notes: {user_notes}")

        payload = self._chat_json(
            system=stylist_system_prompt(language),
            user_content="\n".join(context_lines) or f"Recommend an outfit for {occasion or 'a casual day'}.",
            model=settings.OPENAI_TEXT_MODEL,
            schema_model=RecommendationResult,
        )
        return RecommendationResult.model_validate(payload)

    def design_turn(self, *, message: str, design_state: DesignState | None,
                    language: str = "en") -> DesignTurnResponse:
        from ai.prompts import designer_system_prompt

        payload = self._chat_json(
            system=designer_system_prompt(design_state, language),
            user_content=message,
            model=settings.OPENAI_TEXT_MODEL,
            schema_model=DesignTurnResponse,
        )
        return DesignTurnResponse.model_validate(payload)

    # ---- Wardrobe -------------------------------------------------------
    def recommend_from_wardrobe(self, *, occasion: str | None, budget_inr: int | None,
                                wardrobe_summary: list[dict],
                                style_context: dict | None = None) -> RecommendationResult:
        import json

        from ai.prompts import wardrobe_system_prompt

        context_lines = [
            "The user owns these garments. Build ONE outfit ONLY from these ids:",
            json.dumps(wardrobe_summary),
        ]
        if style_context:
            context_lines.append("User style profile: " + json.dumps(style_context))
        context_lines.append(f"Occasion: {occasion or 'casual'}")
        if budget_inr:
            context_lines.append(f"Budget context (items are already owned): ₹{budget_inr}")
        context_lines.append(
            "Set used_item_ids to the ids of every item you included. "
            "In outfit_components, describe each chosen piece by name."
        )

        payload = self._chat_json(
            system=wardrobe_system_prompt(),
            user_content="\n".join(context_lines),
            model=settings.OPENAI_TEXT_MODEL,
            schema_model=RecommendationResult,
        )
        return RecommendationResult.model_validate(payload)

    # ---- Embeddings -----------------------------------------------------
    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL
            if hasattr(settings, "OPENAI_EMBEDDING_MODEL") else "text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]

    # ---- Voice ----------------------------------------------------------
    def transcribe(self, *, audio_bytes: bytes, language: str = "en") -> dict:
        """Whisper-compatible transcription via the configured provider."""
        from django.core.files.base import ContentFile

        file = ContentFile(audio_bytes, name="audio.webm")
        response = self._client.audio.transcriptions.create(
            model=getattr(settings, "OPENAI_STT_MODEL", "whisper-1"),
            file=file,
            language=None if language == "en" else language,
        )
        return {"text": response.text or "", "language": language, "duration_seconds": None}
