import uuid
from django.contrib.postgres.indexes import GinIndex
from django.conf import settings
from django.db import models
from django.utils import timezone

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=64, default="new", db_index=True)
    data = models.JSONField(default=dict, blank=True)
    schema_version = models.CharField(max_length=32, default="1.0.0")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status", "updated_at"]),
            GinIndex(fields=["data"], name="task_data_gin"),
        ]

    def __str__(self):
        return self.title
