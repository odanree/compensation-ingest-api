import hashlib
import json

from django.db import models


class Survey(models.Model):
    name = models.CharField(max_length=200)
    source = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("source", "year")
        ordering = ["-year"]

    def __str__(self):
        return f"{self.name} ({self.year})"


class SurveySubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
        DUPLICATE = "duplicate", "Duplicate"

    survey = models.ForeignKey(Survey, related_name="submissions", on_delete=models.CASCADE)
    raw_data = models.JSONField()
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def compute_fingerprint(cls, raw_data: dict) -> str:
        canonical = json.dumps(raw_data, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def __str__(self):
        return f"Submission {self.pk} ({self.status})"
