import uuid
from contextvars import ContextVar

from django.http import JsonResponse

request_id_var = ContextVar("request_id", default=None)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """Attach a correlation id to every request for log/trace correlation.

    Honors an incoming X-Request-ID, otherwise generates a UUID4. The id is
    exposed on the response header and available via core.middleware.request_id_var.
    Also converts Django-level 404s on /api/ paths into the JSON error envelope
    (DRF's exception handler only covers views that were successfully routed).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)

        if response.status_code == 404 and request.path.startswith("/api/") and \
                not response.streaming and response.get("Content-Type", "").startswith("text/html"):
            response = JsonResponse(
                {"success": False,
                 "error": {"code": "not_found", "message": "The requested resource was not found."},
                 "request_id": request_id},
                status=404,
            )
        response[REQUEST_ID_HEADER] = request_id
        return response
