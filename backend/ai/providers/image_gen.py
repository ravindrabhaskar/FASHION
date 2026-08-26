"""Image generation provider abstraction.

V1: OpenAI-compatible images API when configured; deterministic local placeholder
rendering (SVG->PNG via Pillow) for the mock provider so the product is fully
walkable without external services.
"""
import base64
import io
import zlib

from django.conf import settings


def _placeholder_png(*, width: int = 768, height: int = 1024,
                     top_hex: str = "#0B6E4F", bottom_hex: str = "#F5EFE6",
                     label: str = "FashionXP Look") -> bytes:
    """Render a tasteful two-tone placeholder with a simple label band.

    Pure-Python PNG encoder (no external image-gen dependency needed for mock).
    """
    def hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    tr, tg, tb = hex_to_rgb(top_hex)
    br, bg, bb = hex_to_rgb(bottom_hex)
    split = int(height * 0.62)

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type per scanline
        t = min(1.0, y / split) if y < split else 1.0
        r = int(tr + (br - tr) * t)
        g = int(tg + (bg - tg) * t)
        b = int(tb + (bb - tb) * t)
        row = bytes((r, g, b)) * width
        raw += row

    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct_pack(len(data)) + tag + data
        return c + struct_pack(zlib.crc32(tag + data) & 0xFFFFFFFF)

    import struct

    def struct_pack(n: int) -> bytes:
        return n.to_bytes(4, "big")

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) \
        + chunk(b"IEND", b"")

    # Stamp the label using Pillow if available (best-effort decoration only).
    try:
        from PIL import Image, ImageDraw

        img = Image.open(io.BytesIO(png)).convert("RGB")
        draw = ImageDraw.Draw(img)
        band_y = height - 90
        draw.rectangle([0, band_y, width, height], fill=(255, 255, 255))
        draw.text((24, band_y + 30), f"{label}", fill=(40, 40, 40))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:  # pragma: no cover
        return png


class MockImageProvider:
    name = "mock"

    def generate(self, *, prompt: str) -> dict:
        """Return {'content_type','bytes','provider_ref'} for the orchestrator to store."""
        palette = ["#0B6E4F", "#1B2A4A", "#7C1E2E", "#D4A017", "#5F9EA0"]
        idx = sum(ord(c) for c in prompt) % len(palette)
        data = _placeholder_png(top_hex=palette[idx], label="FashionXP AI Concept")
        return {
            "content_type": "image/png",
            "bytes": data,
            "provider_ref": "mock://" + str(abs(hash(prompt)) % 10**10),
            "b64_json": None,
        }


class OpenAIImageProvider:
    name = "openai-compatible"

    def generate(self, *, prompt: str) -> dict:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=settings.AI_REQUEST_TIMEOUT_SECONDS * 3,
        )
        result = client.images.generate(
            model=settings.OPENAI_IMAGE_MODEL,
            prompt=prompt[:3900],
            size="1024x1536" if settings.OPENAI_IMAGE_MODEL == "gpt-image-1" else "1024x1792",
            n=1,
            response_format="b64_json",
        )
        b64 = result.data[0].b64_json
        return {
            "content_type": "image/png",
            "bytes": base64.b64decode(b64),
            "provider_ref": getattr(result, "id", "") or "",
            "b64_json": b64,
        }
