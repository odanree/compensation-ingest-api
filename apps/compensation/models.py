from django.db import models


class SystemConfig(models.Model):
    """Normalized solar panel configuration (brand → tier mapping)."""

    panel_brand = models.CharField(max_length=200, unique=True)
    panel_tier_label = models.CharField(max_length=200, db_index=True)
    panel_tier = models.CharField(max_length=50, blank=True)  # standard / premium / premium-plus
    tier_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.panel_tier_label


class Location(models.Model):
    raw_location = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="US")
    metro = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.city}, {self.state}" if self.city else self.state or self.country


class SolarQuote(models.Model):
    """Normalized individual solar installation quote."""

    class InstallerType(models.TextChoices):
        LOCAL = "local", "Local (1–5 crews)"
        REGIONAL = "regional", "Regional (6–20 locations)"
        NATIONAL = "national", "National (21+ locations)"
        UTILITY = "utility", "Utility / Developer"

    submission = models.OneToOneField(
        "surveys.QuoteSubmission",
        on_delete=models.CASCADE,
        related_name="solar_quote",
    )
    system_config = models.ForeignKey(
        SystemConfig, on_delete=models.SET_NULL, null=True, related_name="quotes"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="quotes"
    )
    system_size_band = models.CharField(max_length=50, blank=True, db_index=True)
    system_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, help_text="Total installed cost in USD"
    )
    cost_per_watt = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, help_text="Cost per watt ($/W)"
    )
    incentives_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Estimated federal ITC + state rebates in USD"
    )
    annual_production_kwh = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Estimated annual production in kWh"
    )
    roof_age_years = models.PositiveSmallIntegerField(null=True, blank=True)
    installer_type = models.CharField(
        max_length=20, choices=InstallerType.choices, blank=True, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["system_config", "system_size_band", "installer_type"],
                name="solarquote_config_band_type_idx",
            ),
            models.Index(
                fields=["location", "system_size_band"],
                name="solarquote_location_band_idx",
            ),
        ]

    def __str__(self):
        return f"{self.system_config} @ {self.location} — ${self.cost_per_watt}/W"
