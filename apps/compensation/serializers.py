from rest_framework import serializers

from apps.compensation.models import CompensationRecord, Location, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "title", "normalized_title", "family"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "raw_location", "city", "state", "country", "metro"]


class CompensationRecordSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    survey_source = serializers.CharField(
        source="submission.survey.source", read_only=True
    )
    survey_year = serializers.IntegerField(
        source="submission.survey.year", read_only=True
    )

    class Meta:
        model = CompensationRecord
        fields = [
            "id",
            "role",
            "location",
            "level",
            "base_salary",
            "total_comp",
            "equity_value",
            "bonus",
            "years_experience",
            "company_size",
            "survey_source",
            "survey_year",
            "created_at",
        ]
        read_only_fields = fields


class CompensationSummarySerializer(serializers.Serializer):
    role = serializers.CharField()
    level = serializers.CharField()
    p25 = serializers.FloatField(allow_null=True)
    p50 = serializers.FloatField(allow_null=True)
    p75 = serializers.FloatField(allow_null=True)
    p90 = serializers.FloatField(allow_null=True)
    sample_size = serializers.IntegerField()
