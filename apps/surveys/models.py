import hashlib
import json

from django.db import models


class QuoteSource(models.Model):
    """A source of solar installation quotes (e.g., a specific installer or aggregator).

    Also carries a `handler_key` pointing at which registered ingest handler
    should process submissions from this source — the ingest pipeline in
    apps.surveys is domain-agnostic; each domain plugs in its own handler
    via `@register_ingest_handler(key)` in apps.<domain>.handlers.
    """

    name = models.CharField(max_length=200)
    installer_name = models.CharField(max_length=100)
    quote_year = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
    handler_key = models.CharField(
        max_length=50,
        default="solar_quote",
        db_index=True,
        help_text="Registered ingest handler that processes this source's submissions.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("installer_name", "quote_year")
        ordering = ["-quote_year"]

    def __str__(self):
        return f"{self.name} ({self.quote_year})"


class QuoteSubmission(models.Model):
    """A single raw solar quote submitted for ingestion."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
        DUPLICATE = "duplicate", "Duplicate"

    quote_source = models.ForeignKey(
        QuoteSource, related_name="submissions", on_delete=models.CASCADE
    )
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
