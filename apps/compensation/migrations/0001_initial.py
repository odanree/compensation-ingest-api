from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, unique=True)),
                ("normalized_title", models.CharField(db_index=True, max_length=200)),
                ("family", models.CharField(blank=True, max_length=100)),
                ("level_order", models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_location", models.CharField(max_length=200, unique=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("state", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(default="US", max_length=100)),
                ("metro", models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="CompensationRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("submission", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="compensation_record",
                    to="surveys.surveysubmission",
                )),
                ("role", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="records",
                    to="compensation.role",
                )),
                ("location", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="records",
                    to="compensation.location",
                )),
                ("level", models.CharField(blank=True, db_index=True, max_length=50)),
                ("base_salary", models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ("total_comp", models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ("equity_value", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("bonus", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("years_experience", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("company_size", models.CharField(
                    blank=True,
                    choices=[
                        ("startup", "Startup (1-50)"),
                        ("small", "Small (51-200)"),
                        ("mid", "Mid (201-1000)"),
                        ("large", "Large (1001-5000)"),
                        ("enterprise", "Enterprise (5000+)"),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["role", "level", "company_size"], name="compensation_role_level_size_idx"),
                    models.Index(fields=["location", "level"], name="compensation_loc_level_idx"),
                ],
            },
        ),
    ]
