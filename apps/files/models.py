import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils import timezone


class StoredFile(models.Model):
    """Logical file record. Content is stored in Cloudflare R2."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="files",
    )
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, default="application/octet-stream")
    size = models.BigIntegerField(default=0)
    current_version = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["task", "created_at"]),
            models.Index(fields=["content_type", "created_at"]),
            models.Index(fields=["size", "created_at"]),
            models.Index(fields=["name", "created_at"]),
            models.Index(fields=["is_deleted", "created_at"]),
            GinIndex(fields=["metadata"], name="file_metadata_gin"),
        ]

    def __str__(self):
        return f"{self.name} ({self.id})"


class FileVersion(models.Model):
    """Immutable version record for a StoredFile object in R2."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(
        StoredFile,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    storage_key = models.CharField(max_length=1024, unique=True)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, default="application/octet-stream")
    size = models.BigIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64)
    etag = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_file_versions",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=["file", "version"],
                name="unique_file_version",
            )
        ]
        indexes = [
            models.Index(fields=["file", "version"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["checksum_sha256"]),
        ]

    def __str__(self):
        return f"{self.file_id}:v{self.version}"
