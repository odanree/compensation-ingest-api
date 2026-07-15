from rest_framework import serializers

from apps.compensation.models import Location, SolarQuote, SystemConfig


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ["id", "panel_brand", "panel_tier_label", "panel_tier"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "raw_location", "city", "state", "country", "metro"]


class SolarQuoteSerializer(serializers.ModelSerializer):
    system_config = SystemConfigSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    quote_source_name = serializers.CharField(
        source="submission.quote_source.name", read_only=True
    )
    quote_year = serializers.IntegerField(
        source="submission.quote_source.quote_year", read_only=True
    )

    class Meta:
        model = SolarQuote
        fields = [
            "id",
            "system_config",
            "location",
            "system_size_band",
            "system_cost",
            "cost_per_watt",
            "incentives_value",
            "annual_production_kwh",
            "roof_age_years",
            "installer_type",
            "quote_source_name",
            "quote_year",
            "created_at",
        ]
        read_only_fields = fields


class CostSummarySerializer(serializers.Serializer):
    system_size_band = serializers.CharField()
    state = serializers.CharField()
    p25 = serializers.FloatField(allow_null=True)
    p50 = serializers.FloatField(allow_null=True)
    p75 = serializers.FloatField(allow_null=True)
    p90 = serializers.FloatField(allow_null=True)
    sample_size = serializers.IntegerField()


class SolarQuoteRecordSerializer(serializers.Serializer):
    """Per-record validator for the 'solar_quote' ingest handler.

    Registered via @register_ingest_handler("solar_quote", validator=...) in
    apps.compensation.handlers. Runs on each element of the /api/ingest/
    request body BEFORE any QuoteSubmission is created — so callers get an
    immediate 400 with structured errors rather than a FAILED submission.
    """

    panel_brand = serializers.CharField(required=False, allow_blank=True, default="")
    system_size_kw = serializers.FloatField(required=False, allow_null=True)
    system_size_watts = serializers.IntegerField(required=False, allow_null=True)
    system_cost = serializers.FloatField(required=False, allow_null=True)
    cost_per_watt = serializers.FloatField(required=False, allow_null=True)
    incentives_value = serializers.FloatField(required=False, allow_null=True)
    annual_production_kwh = serializers.FloatField(required=False, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, default="")
    roof_age_years = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=100
    )
    installer_type = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        has_cost = (
            data.get("system_cost") is not None
            or data.get("cost_per_watt") is not None
        )
        if not has_cost:
            raise serializers.ValidationError(
                {"system_cost": "At least one of 'system_cost' or 'cost_per_watt' is required."}
            )
        if data.get("system_cost") is not None and data["system_cost"] <= 0:
            raise serializers.ValidationError(
                {"system_cost": "system_cost must be greater than 0."}
            )
        if data.get("cost_per_watt") is not None and data["cost_per_watt"] <= 0:
            raise serializers.ValidationError(
                {"cost_per_watt": "cost_per_watt must be greater than 0."}
            )
        if data.get("system_size_kw") is not None and data["system_size_kw"] <= 0:
            raise serializers.ValidationError(
                {"system_size_kw": "system_size_kw must be greater than 0."}
            )
        return data
