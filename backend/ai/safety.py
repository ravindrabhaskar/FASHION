"""Safety layer for AI interactions (PRD §43).

V1: deterministic keyword gate + scope enforcement. The system prompts keep
models fashion-focused; this filter is the backstop before/after provider calls.
"""
import re

from core.exceptions import AppError

# Topics outside product scope that must be refused.
OUT_OF_SCOPE_PATTERNS = [
    r"\b(medical|diagnos\w*|disease|symptom)\b",
    r"\b(am i (ugly|fat|thin)|rate my (looks?|body|appearance))\b",
    r"\b(body ?sham\w*)\b",
    r"\b(sexual|nsfw|nude)\b",
    r"\b(polit\w+|religio\w+ debate)\b",
]

REFUSAL_MESSAGE = (
    "I can help with styling, outfits, colors and fashion design. "
    "Let's keep our chat focused on fashion!"
)


def check_input_safety(text: str) -> None:
    """Raise a clean refusal for clearly out-of-scope requests."""
    normalized = (text or "").lower()
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, normalized):
            raise AppError(REFUSAL_MESSAGE, code="ai_out_of_scope")


def sanitize_output_text(text: str) -> str:
    """Strip accidental PII-ish artifacts and control characters from model output."""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text or "")
    return cleaned.strip()
