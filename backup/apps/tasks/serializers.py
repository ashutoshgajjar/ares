from rest_framework import serializers

from apps.common.utils import validate_dynamic_payload
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    data = serializers.JSONField(required=False)
    owner_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Task
        fields = ("id", "owner_id", "title", "description", "status", "schema_version", "data", "created_at", "updated_at")
        read_only_fields = ("id", "owner_id", "created_at", "updated_at")

    def validate_data(self, value):
        validate_dynamic_payload(value)
        return value

    def validate_status(self, value):
        # Default statuses are supported, but custom status values remain valid.
        if len(value.strip()) > 64 or not value.strip():
            raise serializers.ValidationError("status must be a non-empty string of at most 64 characters.")
        return value.strip()

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("title cannot be empty.")
        return value
