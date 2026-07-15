from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("panel_brand", models.CharField(max_length=200, unique=True)),
                ("panel_tier_label", models.CharField(db_index=True, max_length=200)),
                ("panel_tier", models.CharField(blank=True, max_length=50)),
                ("tier_order", models.PositiveSmallIntegerField(default=0)),
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
            name="SolarQuote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("submission", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="solar_quote",
                    to="surveys.quotesubmission",
                )),
                ("system_config", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="quotes",
                    to="compensation.systemconfig",
                )),
                ("location", models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="quotes",
                    to="compensation.location",
                )),
                ("system_size_band", models.CharField(blank=True, db_index=True, max_length=50)),
                ("system_cost", models.DecimalField(
                    decimal_places=2,
                    help_text="Total installed cost in USD",
                    max_digits=10,
                    null=True,
                )),
                ("cost_per_watt", models.DecimalField(
                    decimal_places=3,
                    help_text="Cost per watt ($/W)",
                    max_digits=6,
                    null=True,
                )),
                ("incentives_value", models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text="Estimated federal ITC + state rebates in USD",
                    max_digits=10,
                    null=True,
                )),
                ("annual_production_kwh", models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text="Estimated annual production in kWh",
                    max_digits=10,
                    null=True,
                )),
                ("roof_age_years", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("installer_type", models.CharField(
                    blank=True,
                    choices=[
                        ("local", "Local (1\u20135 crews)"),
                        ("regional", "Regional (6\u201320 locations)"),
                        ("national", "National (21+ locations)"),
                        ("utility", "Utility / Developer"),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["system_config", "system_size_band", "installer_type"],
                        name="sq_config_band_installer_idx",
                    ),
                    models.Index(
                        fields=["location", "system_size_band"],
                        name="solarquote_location_band_idx",
                    ),
                ],
            },
        ),
    ]
