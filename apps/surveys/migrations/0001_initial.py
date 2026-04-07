from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Survey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("source", models.CharField(max_length=100)),
                ("year", models.PositiveSmallIntegerField()),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-year"],
                "unique_together": {("source", "year")},
            },
        ),
        migrations.CreateModel(
            name="SurveySubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("survey", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="submissions",
                    to="surveys.survey",
                )),
                ("raw_data", models.JSONField()),
                ("fingerprint", models.CharField(db_index=True, max_length=64, unique=True)),
                ("status", models.CharField(
                    choices=[
                        ("pending", "Pending"),
                        ("processing", "Processing"),
                        ("processed", "Processed"),
                        ("failed", "Failed"),
                        ("duplicate", "Duplicate"),
                    ],
                    db_index=True,
                    default="pending",
                    max_length=20,
                )),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
