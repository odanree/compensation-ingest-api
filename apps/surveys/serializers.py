from rest_framework import serializers

from apps.surveys.models import Survey, SurveySubmission


class SurveySerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Survey
        fields = ["id", "name", "source", "year", "description", "submission_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SurveySubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveySubmission
        fields = ["id", "survey", "fingerprint", "status", "error_message", "created_at", "processed_at"]
        read_only_fields = ["id", "fingerprint", "status", "error_message", "created_at", "processed_at"]


class IngestRecordSerializer(serializers.Serializer):
    role_title = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True, default="")
    base_salary = serializers.FloatField(required=False, allow_null=True)
    total_comp = serializers.FloatField(required=False, allow_null=True)
    total_compensation = serializers.FloatField(required=False, allow_null=True)
    equity_value = serializers.FloatField(required=False, allow_null=True)
    equity = serializers.FloatField(required=False, allow_null=True)
    bonus = serializers.FloatField(required=False, allow_null=True)
    level = serializers.CharField(required=False, allow_blank=True, default="")
    years_experience = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=50)
    yoe = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=50)
    company_size = serializers.CharField(required=False, allow_blank=True, default="")
    company_headcount = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        role_title = data.get("role_title", "") or data.get("title", "")
        if not role_title:
            raise serializers.ValidationError(
                {"role_title": "At least one of 'role_title' or 'title' is required."}
            )

        total_comp = data.get("total_comp") or data.get("total_compensation")
        if total_comp is not None and total_comp <= 0:
            raise serializers.ValidationError(
                {"total_comp": "total_comp must be greater than 0."}
            )

        base_salary = data.get("base_salary")
        if base_salary is not None and base_salary <= 0:
            raise serializers.ValidationError(
                {"base_salary": "base_salary must be greater than 0."}
            )

        return data


class IngestRequestSerializer(serializers.Serializer):
    survey_id = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=10000,
    )

    def validate_survey_id(self, value):
        from apps.surveys.models import Survey

        if not Survey.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Survey {value} does not exist.")
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
