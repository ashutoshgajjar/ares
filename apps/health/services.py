import logging
from typing import Any

from apps.common.logging import request_id_var
from .models import HealthCheckLog

logger = logging.getLogger(__name__)


def log_health_check_route(
    *,
    request,
    checks: dict[str, Any],
    overall_status: str,
    http_status: int,
    duration_ms: float,
    persist: bool = True,
) -> bool:
    """Write a health-route log and persist it when the database is available.

    Returns True only when the log row was saved. The normal application logger
    remains the fallback when the database check fails or the insert fails.
    Sensitive configuration values and raw exception messages are not stored.
    """
    request_id = request_id_var.get() or request.headers.get("X-Request-ID", "-")
    log_method = logger.info if overall_status == "ok" else logger.warning

    log_method(
        "Health route completed",
        extra={
            "request_id": request_id,
            "route": request.path[:255],
            "method": request.method,
            "health_status": overall_status,
            "http_status": http_status,
            "duration_ms": round(duration_ms, 2),
        },
    )

    if not persist:
        logger.warning(
            "Health route log was not saved because the database check failed",
            extra={"request_id": request_id},
        )
        return False

    try:
        HealthCheckLog.objects.create(
            request_id=request_id[:128],
            route=request.path[:255],
            method=request.method[:10],
            status=overall_status,
            http_status=http_status,
            duration_ms=round(max(duration_ms, 0), 2),
            checks=checks,
        )
        return True
    except Exception as exc:
        # Do not fail the health endpoint if audit-log persistence fails.
        logger.error(
            "Unable to save health route log; error_type=%s",
            type(exc).__name__,
            extra={"request_id": request_id},
            exc_info=True,
        )
        return False
