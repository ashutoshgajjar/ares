import uuid
from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, models
from django.utils import timezone


def create_initial_roles(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("username", models.CharField(blank=True, db_index=True, max_length=150, null=True, unique=True)),
                ("email", models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True)),
                ("role", models.CharField(db_index=True, default="guest", max_length=64)),
                ("account_status", models.CharField(db_index=True, default="active", max_length=64)),
                ("profile", models.JSONField(blank=True, default=dict)),
                ("schema_version", models.CharField(default="1.0.0", max_length=32)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="custom_user_set", related_query_name="custom_user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="custom_user_set", related_query_name="custom_user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"indexes": [models.Index(fields=["role", "is_active"], name="users_user_role_c2d89a_idx"), models.Index(fields=["account_status", "is_active"], name="users_user_account_1c0a2a_idx"), models.Index(fields=["created_at"], name="users_user_created_4c83dd_idx"), GinIndex(fields=["profile"], name="user_profile_gin")]},
        ),
    ]
