import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_submission(self, submission_id: int) -> dict:
    """Dispatch a submission to its registered domain handler.

    Manages the state machine (PENDING → PROCESSING → PROCESSED/FAILED) and
    delegates the actual normalization + persistence to the handler registered
    under `submission.quote_source.handler_key`. Handlers live in
    apps.<domain>.handlers and register via @register_ingest_handler(key).
    """
    from apps.surveys.handlers import UnknownIngestHandler, get_handler
    from apps.surveys.models import QuoteSubmission

    try:
        submission = QuoteSubmission.objects.select_related("quote_source").get(
            pk=submission_id
        )
    except QuoteSubmission.DoesNotExist:
        logger.error("QuoteSubmission %s not found", submission_id)
        return {"status": "error", "message": "not found"}

    if submission.status == QuoteSubmission.Status.PROCESSED:
        return {"status": "skipped", "reason": "already processed"}

    handler_key = submission.quote_source.handler_key
    try:
        handler = get_handler(handler_key)
    except UnknownIngestHandler as exc:
        submission.status = QuoteSubmission.Status.FAILED
        submission.error_message = str(exc)
        submission.save(update_fields=["status", "error_message"])
        logger.error(
            "No ingest handler for submission %s (key=%s)",
            submission_id,
            handler_key,
        )
        return {"status": "error", "message": f"no handler '{handler_key}'"}

    submission.status = QuoteSubmission.Status.PROCESSING
    submission.save(update_fields=["status"])

    try:
        handler(submission)
        submission.status = QuoteSubmission.Status.PROCESSED
        submission.processed_at = timezone.now()
        submission.save(update_fields=["status", "processed_at"])
        return {
            "status": "processed",
            "submission_id": submission_id,
            "handler": handler_key,
        }
    except Exception as exc:
        submission.status = QuoteSubmission.Status.FAILED
        submission.error_message = str(exc)
        submission.save(update_fields=["status", "error_message"])
        logger.exception(
            "Handler '%s' failed on submission %s", handler_key, submission_id
        )
        raise self.retry(exc=exc)


@shared_task
def bulk_ingest_quotes(quote_source_id: int, records: list) -> dict:
    from apps.surveys.models import QuoteSource, QuoteSubmission

    try:
        quote_source = QuoteSource.objects.get(pk=quote_source_id)
    except QuoteSource.DoesNotExist:
        return {"status": "error", "message": f"QuoteSource {quote_source_id} not found"}

    submitted = 0
    duplicates = 0

    for record in records:
        fingerprint = QuoteSubmission.compute_fingerprint(record)
        submission, created = QuoteSubmission.objects.get_or_create(
            fingerprint=fingerprint,
            defaults={"quote_source": quote_source, "raw_data": record},
        )
        if created:
            process_submission.delay(submission.pk)
            submitted += 1
        else:
            duplicates += 1

    return {
        "quote_source_id": quote_source_id,
        "submitted": submitted,
        "duplicates": duplicates,
    }
