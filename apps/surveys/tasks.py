import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_submission(self, submission_id: int) -> dict:
    from apps.compensation.models import CompensationRecord, Location, Role
    from apps.surveys.models import SurveySubmission
    from apps.surveys.normalizers import (
        normalize_company_size,
        normalize_location,
        normalize_role_title,
    )

    try:
        submission = SurveySubmission.objects.select_related("survey").get(pk=submission_id)
    except SurveySubmission.DoesNotExist:
        logger.error("Submission %s not found", submission_id)
        return {"status": "error", "message": "not found"}

    if submission.status == SurveySubmission.Status.PROCESSED:
        return {"status": "skipped", "reason": "already processed"}

    submission.status = SurveySubmission.Status.PROCESSING
    submission.save(update_fields=["status"])

    try:
        data = submission.raw_data

        raw_title = data.get("role_title", data.get("title", ""))
        norm_title, family = normalize_role_title(raw_title)
        role, _ = Role.objects.get_or_create(
            title=raw_title,
            defaults={"normalized_title": norm_title, "family": family},
        )

        raw_loc = data.get("location", "")
        loc_data = normalize_location(raw_loc)
        location, _ = Location.objects.get_or_create(
            raw_location=raw_loc,
            defaults=loc_data,
        )

        def parse_dollars(val) -> float | None:
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            cleaned = str(val).replace("$", "").replace(",", "").replace("k", "000").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None

        CompensationRecord.objects.update_or_create(
            submission=submission,
            defaults={
                "role": role,
                "location": location,
                "level": data.get("level", ""),
                "base_salary": parse_dollars(data.get("base_salary")),
                "total_comp": parse_dollars(
                    data.get("total_comp", data.get("total_compensation"))
                ),
                "equity_value": parse_dollars(
                    data.get("equity_value", data.get("equity"))
                ),
                "bonus": parse_dollars(data.get("bonus")),
                "years_experience": data.get("years_experience", data.get("yoe")),
                "company_size": normalize_company_size(
                    data.get("company_size", data.get("company_headcount", ""))
                ),
            },
        )

        submission.status = SurveySubmission.Status.PROCESSED
        submission.processed_at = timezone.now()
        submission.save(update_fields=["status", "processed_at"])

        return {"status": "processed", "submission_id": submission_id}

    except Exception as exc:
        submission.status = SurveySubmission.Status.FAILED
        submission.error_message = str(exc)
        submission.save(update_fields=["status", "error_message"])
        logger.exception("Failed to process submission %s", submission_id)
        raise self.retry(exc=exc)


@shared_task
def bulk_ingest_survey(survey_id: int, records: list) -> dict:
    from apps.surveys.models import Survey, SurveySubmission

    try:
        survey = Survey.objects.get(pk=survey_id)
    except Survey.DoesNotExist:
        return {"status": "error", "message": f"Survey {survey_id} not found"}

    submitted = 0
    duplicates = 0

    for record in records:
        fingerprint = SurveySubmission.compute_fingerprint(record)
        submission, created = SurveySubmission.objects.get_or_create(
            fingerprint=fingerprint,
            defaults={"survey": survey, "raw_data": record},
        )
        if created:
            process_submission.delay(submission.pk)
            submitted += 1
        else:
            duplicates += 1

    return {
        "survey_id": survey_id,
        "submitted": submitted,
        "duplicates": duplicates,
    }
