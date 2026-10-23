from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ("-created_at",)
    list_display = ("id", "email", "username", "role", "account_status", "is_active", "created_at")
    search_fields = ("email", "username", "id")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = UserAdmin.fieldsets + (("Dynamic profile", {"fields": ("profile", "schema_version", "role", "account_status", "created_at", "updated_at")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Dynamic profile", {"fields": ("email", "username", "profile", "role", "account_status")}),)
