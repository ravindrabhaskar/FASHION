import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "authentication_failed": "Authentication credentials were invalid or expired.",
    "not_authenticated": "Please sign in to continue.",
    "permission_denied": "You do not have permission to perform this action.",
    "not_found": "The requested resource was not found.",
    "method_not_allowed": "This method is not allowed here.",
    "throttled": "Too many requests. Please slow down and try again shortly.",
}


class AppError(Exception):
    """Base class for domain errors mapped to clean API responses."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bad_request"
    default_message = "Request could not be completed."

    def __init__(self, message: str | None = None, *, code: str | None = None,
                 details: dict | None = None, status_code: int | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code


def exception_handler(exc, context):
    """Produce a consistent machine-readable error envelope for every failure."""
    request_id = None
    try:
        from core.middleware import request_id_var

        request_id = request_id_var.get()
    except Exception:  # pragma: no cover - middleware always present in practice
        pass

    if isinstance(exc, AppError):
        payload = {"success": False, "error": {"code": exc.code, "message": exc.message}}
        if exc.details:
            payload["error"]["details"] = exc.details
        if request_id:
            payload["request_id"] = request_id
        return Response(payload, status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled exception", extra={"path": getattr(context.get("request"), "path", "")})
        payload = {
            "success": False,
            "error": {"code": "server_error", "message": "Something went wrong. Please try again."},
        }
        if request_id:
            payload["request_id"] = request_id
        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Normalize DRF errors.
    code_map = {
        status.HTTP_400_BAD_REQUEST: "validation_error",
        status.HTTP_401_UNAUTHORIZED: "authentication_failed",
        status.HTTP_403_FORBIDDEN: "permission_denied",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
    }
    err_code = code_map.get(response.status_code, "error")
    message = ERROR_MESSAGES.get(err_code)
    details = None

    data = response.data
    if isinstance(data, dict) and isinstance(data.get("detail"), str):
        message = message or data["detail"]
    elif isinstance(data, dict):
        details = data
        first_field = next(iter(data), None)
        first_err = data[first_field]
        if isinstance(first_err, list | tuple) and first_err:
            first_err = first_err[0]
        if isinstance(first_err, dict):
            first_err = str(first_err.get("detail", first_err))
        message = message or f"{str(first_field).replace('_', ' ')}: {first_err}"
    elif isinstance(data, list | tuple):
        details = {"non_field_errors": list(data)}
        message = message or "; ".join(str(x) for x in data)

    payload = {"success": False, "error": {"code": err_code, "message": message or "Request failed."}}
    if details:
        payload["error"]["details"] = details
    if request_id:
        payload["request_id"] = request_id
    return Response(payload, status=response.status_code)


# Re-export common DRF exceptions for convenience in views.
PermissionDeniedError = PermissionDenied
NotFound = Http404
NotAuthenticated = exceptions.NotAuthenticated


def validation_error(message: str, *, code: str = "validation_error") -> AppError:
    return AppError(message, code=code)
