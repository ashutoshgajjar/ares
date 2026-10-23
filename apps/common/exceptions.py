# import logging

# from rest_framework import status
# from rest_framework.exceptions import ErrorDetail
# from rest_framework.views import exception_handler

# logger = logging.getLogger(__name__)


# def _normalize(detail):
#     if isinstance(detail, ErrorDetail):
#         return str(detail)
#     if isinstance(detail, dict):
#         return {str(k): _normalize(v) for k, v in detail.items()}
#     if isinstance(detail, list):
#         return [_normalize(v) for v in detail]
#     return detail


# def custom_exception_handler(exc, context):
#     response = exception_handler(exc, context)
#     request = context.get("request")
#     request_id = request.headers.get("X-Request-ID", "-") if request else "-"

#     if response is not None:
#         response.data = {
#             "error": {
#                 "code": getattr(exc, "default_code", "api_error"),
#                 "message": _normalize(response.data),
#                 "request_id": request_id,
#             }
#         }
#         return response

#     logger.exception("Unhandled API exception", extra={"request_id": request_id})
#     from rest_framework.response import Response
#     return Response(
#         {"error": {"code": "internal_server_error", "message": "An internal server error occurred.", "request_id": request_id}},
#         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#     )

import logging

from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _normalize(detail):
    if isinstance(detail, ErrorDetail):
        return str(detail)
    if isinstance(detail, dict):
        return {str(key): _normalize(value) for key, value in detail.items()}
    if isinstance(detail, list):
        return [_normalize(value) for value in detail]
    return detail


def _get_token_error_message(data):
    """Return the most useful SimpleJWT error message without nested metadata."""
    if not isinstance(data, dict):
        return _normalize(data)

    messages = data.get("messages")
    if isinstance(messages, list) and messages:
        first = messages[0]
        if isinstance(first, dict) and first.get("message"):
            return _normalize(first["message"])

    detail = data.get("detail")
    if detail:
        return _normalize(detail)

    return _normalize(data)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = request.headers.get("X-Request-ID", "-") if request else "-"
    code = getattr(exc, "default_code", "api_error")

    if response is not None:
        if code == "token_not_valid":
            message = _get_token_error_message(response.data)
        else:
            message = _normalize(response.data)

        response.data = {
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        }
        return response

    logger.exception("Unhandled API exception", extra={"request_id": request_id})
    from rest_framework.response import Response

    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An internal server error occurred.",
                "request_id": request_id,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )