from django.contrib import admin

from .models import HealthCheckLog


@admin.register(HealthCheckLog)
class HealthCheckLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "status",
        "http_status",
        "duration_ms",
        "method",
        "route",
        "request_id",
    )
    list_filter = ("status", "http_status", "created_at")
    search_fields = ("request_id", "route")
    readonly_fields = (
        "request_id",
        "route",
        "method",
        "status",
        "http_status",
        "duration_ms",
        "checks",
        "created_at",
    )
    date_hierarchy = "created_at"
