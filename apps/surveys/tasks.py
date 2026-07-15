import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_quote(self, submission_id: int) -> dict:
    from apps.compensation.models import Location, SolarQuote, SystemConfig
    from apps.surveys.models import QuoteSubmission
    from apps.surveys.normalizers import (
        normalize_installer_type,
        normalize_location,
        normalize_panel_brand,
        normalize_system_size_band,
    )

    try:
        submission = QuoteSubmission.objects.select_related("quote_source").get(
            pk=submission_id
        )
    except QuoteSubmission.DoesNotExist:
        logger.error("QuoteSubmission %s not found", submission_id)
        return {"status": "error", "message": "not found"}

    if submission.status == QuoteSubmission.Status.PROCESSED:
        return {"status": "skipped", "reason": "already processed"}

    submission.status = QuoteSubmission.Status.PROCESSING
    submission.save(update_fields=["status"])

    try:
        data = submission.raw_data

        # --- Panel / system config ---
        raw_brand = data.get("panel_brand", "")
        tier_label, panel_tier, tier_order = normalize_panel_brand(raw_brand)
        system_config, _ = SystemConfig.objects.get_or_create(
            panel_brand=raw_brand or "Unknown",
            defaults={
                "panel_tier_label": tier_label,
                "panel_tier": panel_tier,
                "tier_order": tier_order,
            },
        )

        # --- Location ---
        raw_loc = data.get("location", "")
        loc_data = normalize_location(raw_loc)
        location, _ = Location.objects.get_or_create(
            raw_location=raw_loc or "Unknown",
            defaults=loc_data,
        )

        # --- System size band ---
        watts = None
        if data.get("system_size_watts"):
            watts = float(data["system_size_watts"])
        elif data.get("system_size_kw"):
            watts = float(data["system_size_kw"]) * 1000
        system_size_band = normalize_system_size_band(watts) if watts else ""

        # --- Costs ---
        def parse_float(val) -> float | None:
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            cleaned = str(val).replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None

        system_cost = parse_float(data.get("system_cost"))
        cost_per_watt = parse_float(data.get("cost_per_watt"))

        # Derive cost_per_watt from system_cost + size if not provided
        if cost_per_watt is None and system_cost is not None and watts:
            cost_per_watt = round(system_cost / watts, 3)

        SolarQuote.objects.update_or_create(
            submission=submission,
            defaults={
                "system_config": system_config,
                "location": location,
                "system_size_band": system_size_band,
                "system_cost": system_cost,
                "cost_per_watt": cost_per_watt,
                "incentives_value": parse_float(data.get("incentives_value")),
                "annual_production_kwh": parse_float(data.get("annual_production_kwh")),
                "roof_age_years": data.get("roof_age_years"),
                "installer_type": normalize_installer_type(
                    data.get("installer_type", data.get("installer", ""))
                ),
            },
        )

        submission.status = QuoteSubmission.Status.PROCESSED
        submission.processed_at = timezone.now()
        submission.save(update_fields=["status", "processed_at"])

        return {"status": "processed", "submission_id": submission_id}

    except Exception as exc:
        submission.status = QuoteSubmission.Status.FAILED
        submission.error_message = str(exc)
        submission.save(update_fields=["status", "error_message"])
        logger.exception("Failed to process quote submission %s", submission_id)
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
            process_quote.delay(submission.pk)
            submitted += 1
        else:
            duplicates += 1

    return {
        "quote_source_id": quote_source_id,
        "submitted": submitted,
        "duplicates": duplicates,
    }
