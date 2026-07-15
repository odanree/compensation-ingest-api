from rest_framework import serializers

from apps.surveys.handlers import get_record_validator
from apps.surveys.models import QuoteSource, QuoteSubmission


class QuoteSourceSerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = QuoteSource
        fields = [
            "id", "name", "installer_name", "quote_year",
            "description", "handler_key", "submission_count",
            "created_at", "updated_at",
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


class IngestRequestSerializer(serializers.Serializer):
    """Generic ingest envelope: quote_source_id + list of records.

    Per-record shape validation is delegated to whichever DRF Serializer the
    source's handler registered as its `validator` in
    apps.<domain>.handlers. If the handler registered no validator, records
    pass through untyped and the handler is expected to validate at
    dispatch time.
    """

    quote_source_id = serializers.IntegerField()
    records = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=100,
    )

    def validate(self, data):
        try:
            source = QuoteSource.objects.get(pk=data["quote_source_id"])
        except QuoteSource.DoesNotExist:
            raise serializers.ValidationError(
                {"quote_source_id": f"QuoteSource {data['quote_source_id']} does not exist."}
            )

        validator_cls = get_record_validator(source.handler_key)
        if validator_cls is None:
            return data

        errors = []
        for i, record in enumerate(data["records"]):
            s = validator_cls(data=record)
            if not s.is_valid():
                errors.append({"index": i, "errors": s.errors})
        if errors:
            raise serializers.ValidationError({"records": errors})
        return data
