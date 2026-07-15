"""Solar-quote ingest handler — the domain layer's plugin into apps.surveys.

Registers under the key "solar_quote" (the default value for
QuoteSource.handler_key, so existing sources keep working transparently).

The generic pipeline in apps.surveys owns fingerprint dedup, the Celery
fan-out, the state machine and retry policy. This handler only owns:
brand → tier, location → metro, size → band, cost derivation, and the
final upsert into SolarQuote.
"""
from apps.surveys.handlers import register_ingest_handler


@register_ingest_handler("solar_quote")
def solar_quote_handler(submission) -> None:
    from apps.compensation.models import Location, SolarQuote, SystemConfig
    from apps.surveys.normalizers import (
        normalize_installer_type,
        normalize_location,
        normalize_panel_brand,
        normalize_system_size_band,
    )

    data = submission.raw_data

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

    raw_loc = data.get("location", "")
    loc_data = normalize_location(raw_loc)
    location, _ = Location.objects.get_or_create(
        raw_location=raw_loc or "Unknown",
        defaults=loc_data,
    )

    watts = None
    if data.get("system_size_watts"):
        watts = float(data["system_size_watts"])
    elif data.get("system_size_kw"):
        watts = float(data["system_size_kw"]) * 1000
    system_size_band = normalize_system_size_band(watts) if watts else ""

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
