from django.db import models


class Role(models.Model):
    title = models.CharField(max_length=200, unique=True)
    normalized_title = models.CharField(max_length=200, db_index=True)
    family = models.CharField(max_length=100, blank=True)
    level_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.normalized_title


class Location(models.Model):
    raw_location = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="US")
    metro = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.city}, {self.state}" if self.city else self.country


class CompensationRecord(models.Model):
    class CompanySize(models.TextChoices):
        STARTUP = "startup", "Startup (1-50)"
        SMALL = "small", "Small (51-200)"
        MID = "mid", "Mid (201-1000)"
        LARGE = "large", "Large (1001-5000)"
        ENTERPRISE = "enterprise", "Enterprise (5000+)"

    submission = models.OneToOneField(
        "surveys.SurveySubmission",
        on_delete=models.CASCADE,
        related_name="compensation_record",
    )
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, related_name="records"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="records"
    )
    level = models.CharField(max_length=50, blank=True, db_index=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_comp = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    equity_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    company_size = models.CharField(
        max_length=20, choices=CompanySize.choices, blank=True, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["role", "level", "company_size"]),
            models.Index(fields=["location", "level"]),
        ]

    def __str__(self):
        return f"{self.role} @ {self.location} - ${self.total_comp}"
