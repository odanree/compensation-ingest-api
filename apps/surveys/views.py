from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from config.throttles import CloudflareScopedRateThrottle

from apps.surveys.filters import QuoteSourceFilter, QuoteSubmissionFilter
from apps.surveys.models import QuoteSource, QuoteSubmission
from apps.surveys.serializers import (
    IngestRequestSerializer,
    QuoteSourceSerializer,
    QuoteSubmissionSerializer,
)
from apps.surveys.tasks import process_quote


class QuoteSourceListCreateView(generics.ListCreateAPIView):
    serializer_class = QuoteSourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = QuoteSourceFilter
    ordering_fields = ["quote_year", "created_at"]

    def get_queryset(self):
        return QuoteSource.objects.annotate(
            submission_count=Count("submissions")
        ).order_by("-quote_year")


class QuoteSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuoteSourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return QuoteSource.objects.annotate(submission_count=Count("submissions"))


class IngestView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CloudflareScopedRateThrottle]
    throttle_scope = "ingest"
    serializer_class = IngestRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quote_source_id = serializer.validated_data["quote_source_id"]
        records = serializer.validated_data["records"]
        quote_source = QuoteSource.objects.get(pk=quote_source_id)

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

        return Response(
            {
                "quote_source_id": quote_source_id,
                "submitted": submitted,
                "duplicates": duplicates,
            },
            status=status.HTTP_201_CREATED if submitted > 0 else status.HTTP_200_OK,
        )


class QuoteSubmissionListView(generics.ListAPIView):
    serializer_class = QuoteSubmissionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = QuoteSubmissionFilter
    ordering_fields = ["created_at", "processed_at"]

    def get_queryset(self):
        return QuoteSubmission.objects.select_related("quote_source").order_by(
            "-created_at"
        )
