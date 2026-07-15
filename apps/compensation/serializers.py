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
