from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.surveys.filters import SurveyFilter, SurveySubmissionFilter
from apps.surveys.models import Survey, SurveySubmission
from apps.surveys.serializers import (
    IngestRequestSerializer,
    SurveySerializer,
    SurveySubmissionSerializer,
)
from apps.surveys.tasks import process_submission


class SurveyListCreateView(generics.ListCreateAPIView):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = SurveyFilter
    ordering_fields = ["year", "created_at"]

    def get_queryset(self):
        return Survey.objects.annotate(submission_count=Count("submissions")).order_by("-year")


class SurveyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Survey.objects.annotate(submission_count=Count("submissions"))


class IngestView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = IngestRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        survey_id = serializer.validated_data["survey_id"]
        records = serializer.validated_data["records"]
        survey = Survey.objects.get(pk=survey_id)

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

        return Response(
            {
                "survey_id": survey_id,
                "submitted": submitted,
                "duplicates": duplicates,
            },
            status=status.HTTP_201_CREATED if submitted > 0 else status.HTTP_200_OK,
        )


class SubmissionListView(generics.ListAPIView):
    serializer_class = SurveySubmissionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = SurveySubmissionFilter
    ordering_fields = ["created_at", "processed_at"]

    def get_queryset(self):
        return SurveySubmission.objects.select_related("survey").order_by("-created_at")
