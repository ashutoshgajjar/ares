from django.db import models


class HealthCheckLog(models.Model):
    """Persist one summary for each health endpoint request."""

    STATUS_CHOICES = (
        ("ok", "OK"),
        ("degraded", "Degraded"),
    )

    id = models.BigAutoField(primary_key=True)
    request_id = models.CharField(max_length=128, default="-", blank=True)
    route = models.CharField(max_length=255, default="/api/v1/health/")
    method = models.CharField(max_length=10, default="GET")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    http_status = models.PositiveSmallIntegerField()
    duration_ms = models.FloatField(default=0)
    checks = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="healthlog_status_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.created_at.isoformat()} {self.status} {self.route}"
