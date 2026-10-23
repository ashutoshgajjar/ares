from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "schema_version", "created_at", "updated_at")
    list_filter = ("status", "schema_version")
    search_fields = ("title", "description", "owner__email", "owner__username")
    readonly_fields = ("created_at", "updated_at")
