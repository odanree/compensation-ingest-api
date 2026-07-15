"""Job-post ingest handler — Phase 1 skeleton demonstrating the extension point.

This handler exists to prove that apps.surveys is truly domain-agnostic: a
second consumer app can plug in a new handler_key without touching the
ingest pipeline, the state machine, the fingerprint logic, or the API.

Phase 1 scope: validate the record has a `title`, log it, and return —
the submission ends up in PROCESSED status with no domain rows created.

Phase 2 will introduce a real JobListing model, salary-band analytics, and
its own DRF endpoints — see docs/adr/0005-ingest-core-extraction.md.
"""
import logging

from rest_framework import serializers

from apps.surveys.handlers import register_ingest_handler

logger = logging.getLogger(__name__)


class JobPostRecordSerializer(serializers.Serializer):
    """Per-record validator for the 'job_post' handler.

    Minimal in Phase 1 — just requires a `title`. Phase 2 will grow this
    into the full job-listing schema (company, salary_min/max, currency,
    location, posted_at, source_url) alongside the JobListing model.
    """

    title = serializers.CharField(max_length=200)
    company = serializers.CharField(required=False, allow_blank=True, default="")
    location = serializers.CharField(required=False, allow_blank=True, default="")
    salary_min = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    salary_max = serializers.IntegerField(required=False, allow_null=True, min_value=0)


@register_ingest_handler("job_post", validator=JobPostRecordSerializer)
def job_post_handler(submission) -> None:
    data = submission.raw_data
    logger.info(
        "job_post ingested: submission=%s title=%r company=%r",
        submission.pk,
        data.get("title"),
        data.get("company"),
    )
