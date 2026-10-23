from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HealthCheckLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("request_id", models.CharField(blank=True, default="-", max_length=128)),
                ("route", models.CharField(default="/api/v1/health/", max_length=255)),
                ("method", models.CharField(default="GET", max_length=10)),
                ("status", models.CharField(choices=[("ok", "OK"), ("degraded", "Degraded")], db_index=True, max_length=16)),
                ("http_status", models.PositiveSmallIntegerField()),
                ("duration_ms", models.FloatField(default=0)),
                ("checks", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [
                    models.Index(fields=["status", "created_at"], name="healthlog_status_created_idx"),
                ],
            },
        ),
    ]
