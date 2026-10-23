import logging
from time import perf_counter

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import DynamicLimitOffsetPagination
from .models import HealthCheckLog
from .serializers import HealthCheckLogSerializer

from apps.files.storage import R2StorageError, get_r2_storage_service
from .services import log_health_check_route

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Health - OLD Code
# ----------------------------------------------------------------------

# class HealthView(generics.GenericAPIView):
#     """
#     GET /api/v1/health/
#     """

#     permission_classes = [
#         permissions.AllowAny
#     ]

#     authentication_classes = []

#     def get(self, request):
#         try:
#             with connection.cursor() as cursor:
#                 cursor.execute("SELECT 1")
#                 cursor.fetchone()

#             return Response(
#                 {
#                     "status": "ok",
#                     "database": "ok",
#                 }
#             )

#         except Exception:
#             logger.exception(
#                 "Health check database failure"
#             )

#             return Response(
#                 {
#                     "status": "degraded",
#                     "database": "unavailable",
#                 },
#                 status=(
#                     status.HTTP_503_SERVICE_UNAVAILABLE
#                 ),
#             )



class HealthView(APIView):
    """Report API, PostgreSQL, and Cloudflare R2 readiness."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _check_database() -> dict:
        started = perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {
                "status": "ok",
                "latency_ms": round((perf_counter() - started) * 1000, 2),
            }
        except Exception as exc:
            logger.warning(
                "Health database check failed; error_type=%s",
                type(exc).__name__,
                exc_info=True,
            )
            return {
                "status": "unavailable",
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "message": "Database connectivity check failed.",
            }

    @staticmethod
    def _check_cloudflare_r2() -> dict:
        started = perf_counter()
        object_key = getattr(settings, "R2_HEALTHCHECK_KEY", "").strip()

        if not object_key:
            return {
                "status": "not_configured",
                "latency_ms": 0,
                "message": "Set R2_HEALTHCHECK_KEY to the key of an existing R2 object.",
            }

        try:
            get_r2_storage_service().check_health(object_key)
            return {
                "status": "ok",
                "latency_ms": round((perf_counter() - started) * 1000, 2),
            }
        except R2StorageError as exc:
            cause = exc.__cause__
            error_code = None
            http_status = None
            message = "Cloudflare R2 health check failed."

            if isinstance(cause, ClientError):
                response = cause.response
                error_code = response.get("Error", {}).get("Code")
                http_status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if str(http_status) == "403" or error_code in {"403", "AccessDenied"}:
                    message = "R2 denied access to the configured health-check object."
                elif str(http_status) == "404" or error_code in {"404", "NoSuchKey", "NotFound"}:
                    message = "The configured R2 health-check object was not found."
            elif isinstance(cause, BotoCoreError):
                message = "The R2 endpoint could not be reached."
            else:
                message = "R2 storage is not configured correctly."

            logger.warning(
                "Cloudflare R2 health check failed; error_type=%s, error_code=%s, http_status=%s",
                type(cause).__name__ if cause else type(exc).__name__,
                error_code or "unknown",
                http_status or "unknown",
            )
            return {
                "status": "unavailable",
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "message": message,
                **({"error_code": str(error_code)} if error_code is not None else {}),
                **({"http_status": int(http_status)} if http_status is not None else {}),
            }
        except Exception as exc:
            logger.warning(
                "Unexpected R2 health check failure; error_type=%s",
                type(exc).__name__,
                exc_info=True,
            )
            return {
                "status": "unavailable",
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "message": "Cloudflare R2 health check failed.",
            }

    def get(self, request, *args, **kwargs):
        started = perf_counter()
        checks = {
            "api": {"status": "ok"},
            "database": self._check_database(),
            "cloudflare_r2": self._check_cloudflare_r2(),
        }
        healthy = all(item["status"] == "ok" for item in checks.values())
        overall_status = "ok" if healthy else "degraded"
        http_status = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        duration_ms = round((perf_counter() - started) * 1000, 2)

        log_saved = log_health_check_route(
            request=request,
            checks=checks,
            overall_status=overall_status,
            http_status=http_status,
            duration_ms=duration_ms,
            persist=checks["database"]["status"] == "ok",
        )

        return Response(
            {
                "status": overall_status,
                "checks": checks,
                "duration_ms": duration_ms,
                "timestamp": timezone.now().isoformat(),
                "logging": {"persisted": log_saved},
            },
            status=http_status,
        )


class HealthCheckLogListView(generics.ListAPIView):
    """Return saved health-check logs."""

    serializer_class = HealthCheckLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = DynamicLimitOffsetPagination

    queryset = HealthCheckLog.objects.all().order_by("-created_at")