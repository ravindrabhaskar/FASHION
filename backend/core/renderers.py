from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """Wrap successful responses in {"success": true, "data": ...}.

    Error responses (already shaped by core.exceptions) and explicitly
    enveloped payloads pass through untouched.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None
        if response is not None and 200 <= response.status_code < 300:
            if isinstance(data, dict) and ("data" in data or "error" in data):
                pass  # already enveloped
            else:
                data = {"success": True, "data": data}
        return super().render(data, accepted_media_type, renderer_context)
