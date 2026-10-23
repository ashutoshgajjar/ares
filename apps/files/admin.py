from django.contrib import admin

from .models import FileVersion, StoredFile


class FileVersionInline(admin.TabularInline):
    model = FileVersion
    extra = 0
    readonly_fields = (
        "id",
        "version",
        "storage_key",
        "original_name",
        "content_type",
        "size",
        "checksum_sha256",
        "etag",
        "created_by",
        "created_at",
    )


@admin.register(StoredFile)
class StoredFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "task",
        "content_type",
        "size",
        "current_version",
        "is_deleted",
        "created_at",
    )
    list_filter = ("content_type", "is_deleted", "created_at")
    search_fields = ("name", "user__email", "user__username", "task__title", "id")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "current_version")
    inlines = [FileVersionInline]
