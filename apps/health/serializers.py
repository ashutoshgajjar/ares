from rest_framework import serializers

from .models import HealthCheckLog


class HealthCheckLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthCheckLog
        fields = (
            "id",
            "request_id",
            "route",
            "method",
            "status",
            "http_status",
            "duration_ms",
            "checks",
            "created_at",
        )
        read_only_fields = fields