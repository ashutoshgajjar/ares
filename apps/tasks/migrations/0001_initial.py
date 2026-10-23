import uuid
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion
from django.contrib.postgres.indexes import GinIndex

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("status", models.CharField(db_index=True, default="new", max_length=64)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("schema_version", models.CharField(default="1.0.0", max_length=32)),
                ("created_at", models.DateTimeField(default=timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(fields=["owner", "status"], name="tasks_task_owner_i_eb0f3b_idx"),
                    models.Index(fields=["created_at"], name="tasks_task_created_0bb1d3_idx"),
                    models.Index(fields=["status", "updated_at"], name="tasks_task_status_75abf5_idx"),
                    GinIndex(fields=["data"], name="task_data_gin"),
                ],
            },
        ),
    ]
