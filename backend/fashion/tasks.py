"""Async AI image rendering (runs on Celery workers; eager in dev/test)."""
import logging

from celery import shared_task
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10, acks_late=True)
def render_outfit_image(self, outfit_id: str) -> str | None:
    from fashion.models import GeneratedOutfit

    try:
        outfit = GeneratedOutfit.objects.get(id=outfit_id)
    except GeneratedOutfit.DoesNotExist:
        logger.warning("render_outfit_image: outfit %s vanished", outfit_id)
        return None

    if outfit.status == GeneratedOutfit.Status.COMPLETED and outfit.image:
        return str(outfit.id)  # idempotent

    outfit.status = GeneratedOutfit.Status.GENERATING
    outfit.save(update_fields=["status", "updated_at"])

    prompt = outfit.image_prompt or _default_prompt(outfit)
    try:
        from ai import orchestrator

        payload = orchestrator.generate_outfit_image(prompt=prompt)
        name = f"outfits/{outfit_id}.png"
        outfit.image.save(name, ContentFile(payload["bytes"]), save=False)
        outfit.image.name = name
        outfit.status = GeneratedOutfit.Status.COMPLETED
        outfit.failed_reason = ""
        outfit.save(update_fields=["image", "status", "failed_reason", "updated_at"])
        return str(outfit.id)
    except Exception as exc:  # retry then fail gracefully (PRD §55 states)
        logger.exception("Image render failed for outfit %s", outfit_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc
        outfit.status = GeneratedOutfit.Status.FAILED
        outfit.failed_reason = "Image generation failed. You can retry."
        outfit.save(update_fields=["status", "failed_reason", "updated_at"])
        return str(outfit.id)


def _default_prompt(outfit) -> str:
    design = outfit.design_state or {}
    base = design.get("base_color", "")
    garment = design.get("garment_type", "outfit").replace("-", " ")
    return (
        f"Elegant fashion concept illustration of a {base} {garment}, "
        "editorial studio photography, clean background."
    )
