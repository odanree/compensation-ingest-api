from rest_framework import serializers

from apps.surveys.models import QuoteSource, QuoteSubmission


class QuoteSourceSerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = QuoteSource
        fields = [
            "id", "name", "installer_name", "quote_year",
            "description", "submission_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuoteSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteSubmission
        fields = [
            "id", "quote_source", "fingerprint", "status",
            "error_message", "created_at", "processed_at",
        ]
        read_only_fields = [
            "id", "fingerprint", "status", "error_message",
            "created_at", "processed_at",
        ]


class IngestRecordSerializer(serializers.Serializer):
    """Validates a single raw solar quote record."""

    # Panel / system
    panel_brand = serializers.CharField(required=False, allow_blank=True, default="")
    system_size_kw = serializers.FloatField(required=False, allow_null=True)
    system_size_watts = serializers.IntegerField(required=False, allow_null=True)

    # Costs
    system_cost = serializers.FloatField(required=False, allow_null=True)
    cost_per_watt = serializers.FloatField(required=False, allow_null=True)
    incentives_value = serializers.FloatField(required=False, allow_null=True)

    # Production estimate
    annual_production_kwh = serializers.FloatField(required=False, allow_null=True)

    # Property
    location = serializers.CharField(required=False, allow_blank=True, default="")
    roof_age_years = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=100
    )

    # Installer
    installer_type = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        # Need at least one cost signal
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


class IngestRequestSerializer(serializers.Serializer):
    quote_source_id = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=100,
    )

    def validate_quote_source_id(self, value):
        if not QuoteSource.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"QuoteSource {value} does not exist.")
        return value

    def validate_records(self, records):
        validated = []
        errors = []
        for i, record in enumerate(records):
            s = IngestRecordSerializer(data=record)
            if s.is_valid():
                validated.append(record)
            else:
                errors.append({"index": i, "errors": s.errors})
        if errors:
            raise serializers.ValidationError(errors)
        return validated
