"""AI utility endpoints: voice transcription."""
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedActive
from ai import orchestrator
from core.exceptions import AppError


class TranscribeView(APIView):
    """POST multipart `audio` → {text} for voice-driven styling (PRD §42)."""

    permission_classes = [IsAuthenticatedActive]
    throttle_scope = "ai"

    def post(self, request):
        audio = request.FILES.get("audio")
        if not audio:
            raise AppError("An audio file is required.", code="audio_required")
        if audio.size > 15 * 1024 * 1024:
            raise AppError("Voice notes must be under 15 MB.", code="audio_too_large")
        language = str(request.data.get("language", "en") or "en")[:8]
        result = orchestrator.transcribe(
            user=request.user, audio_bytes=audio.read(), language=language
        )
        return Response({"text": result.get("text", ""), "language": result.get("language", language)})
