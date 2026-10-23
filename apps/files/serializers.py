import json

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.common.utils import validate_dynamic_payload
from apps.tasks.models import Task
from apps.users.models import User
from .models import FileVersion, StoredFile
from .storage import R2StorageError, get_r2_storage_service


class MetadataField(serializers.JSONField):
    """Accept JSON objects in both application/json and multipart/form-data requests."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError("metadata must be valid JSON.") from exc
        try:
            validate_dynamic_payload(data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return super().to_internal_value(data)


class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = (
            "id",
            "version",
            "original_name",
            "content_type",
            "size",
            "checksum_sha256",
            "etag",
            "metadata",
            "created_by",
            "created_at",
        )
        read_only_fields = fields

class FileSummarySerializer(serializers.ModelSerializer):
    """
    Compact file representation used inside user responses.

    Does not generate a presigned R2 URL.
    The client can call:
        GET /api/v1/files/{id}/download-url/
    when it needs to download the file.
    """

    task_id = serializers.UUIDField(
        source="task.id",
        read_only=True,
    )

    class Meta:
        model = StoredFile

        fields = (
            "id",
            "task_id",
            "name",
            "content_type",
            "size",
            "current_version",
            "metadata",
            "created_at",
            "updated_at",
        )

        read_only_fields = fields

class StoredFileSerializer(serializers.ModelSerializer):
    task_id = serializers.UUIDField(source="task.id", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    metadata = MetadataField(required=False)
    current_version_detail = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = StoredFile
        fields = (
            "id",
            "user_id",
            "task_id",
            "name",
            "content_type",
            "size",
            "current_version",
            "metadata",
            "is_deleted",
            "created_at",
            "updated_at",
            "deleted_at",
            "current_version_detail",
            "download_url",
        )
        read_only_fields = fields

    def get_current_version_detail(self, obj):
        versions = getattr(obj, "prefetched_versions", None)
        if versions is not None:
            version = next((item for item in versions if item.version == obj.current_version), None)
        else:
            version = obj.versions.filter(version=obj.current_version).first()
        return FileVersionSerializer(version).data if version else None

    def get_download_url(self, obj):
        if obj.is_deleted:
            return None
        request = self.context.get("request")
        if not request or self.context.get("include_download_url") is not True:
            return None
        version = obj.versions.filter(version=obj.current_version).first()
        if not version:
            return None
        try:
            return get_r2_storage_service().presigned_download_url(
                version.storage_key,
                version.original_name,
                version.content_type,
            )
        except R2StorageError:
            return None


class FileCreateSerializer(serializers.Serializer):
    file = serializers.FileField(required=True, allow_empty_file=False)
    name = serializers.CharField(required=False, max_length=255)
    task_id = serializers.UUIDField(required=False, allow_null=True)
    user_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    metadata = MetadataField(required=False)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        requested_user_id = attrs.get("user_id")
        target_user = user

        if requested_user_id:
            if not (user.is_superuser or user.role == "admin"):
                raise serializers.ValidationError({"user_id": "Only administrators can upload files for another user."})
            try:
                target_user = User.objects.get(id=requested_user_id)
            except User.DoesNotExist as exc:
                raise serializers.ValidationError({"user_id": "User not found."}) from exc

        task = None
        if attrs.get("task_id"):
            try:
                task = Task.objects.select_related("owner").get(id=attrs["task_id"])
            except Task.DoesNotExist as exc:
                raise serializers.ValidationError({"task_id": "Task not found."}) from exc
            if not (user.is_superuser or user.role == "admin") and task.owner_id != user.id:
                raise serializers.ValidationError({"task_id": "You do not have access to this task."})
            if task.owner_id != target_user.id:
                raise serializers.ValidationError({"task_id": "The task must belong to the target user."})

        uploaded = attrs["file"]
        max_size = int(getattr(settings, "R2_MAX_UPLOAD_SIZE", 100 * 1024 * 1024))
        if uploaded.size > max_size:
            raise serializers.ValidationError({"file": f"File exceeds the configured maximum size of {max_size} bytes."})

        attrs["target_user"] = target_user
        attrs["task"] = task
        return attrs


class FileMetadataUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    metadata = MetadataField(required=False)


class FileReplaceSerializer(FileMetadataUpdateSerializer):
    file = serializers.FileField(required=True, allow_empty_file=False)


class FileFilterSerializer(serializers.Serializer):
    # Query parameter validation is done in the view to keep dynamic sort/filter support explicit.
    pass
