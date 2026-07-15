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

from apps.surveys.handlers import register_ingest_handler

logger = logging.getLogger(__name__)


@register_ingest_handler("job_post")
def job_post_handler(submission) -> None:
    data = submission.raw_data
    title = (data.get("title") or "").strip()
    if not title:
        raise ValueError("job_post record missing required field: title")
    logger.info(
        "job_post ingested: submission=%s title=%r company=%r",
        submission.pk,
        title,
        data.get("company"),
    )
