from django.db import connection
from rest_framework import generics, views
from rest_framework.response import Response

from apps.compensation.filters import CompensationRecordFilter
from apps.compensation.models import CompensationRecord
from apps.compensation.serializers import (
    CompensationRecordSerializer,
    CompensationSummarySerializer,
)


class CompensationRecordListView(generics.ListAPIView):
    serializer_class = CompensationRecordSerializer
    filterset_class = CompensationRecordFilter
    ordering_fields = ["total_comp", "base_salary", "years_experience", "created_at"]

    def get_queryset(self):
        return CompensationRecord.objects.select_related(
            "role", "location", "submission__survey"
        ).order_by("-total_comp")


class CompensationSummaryView(views.APIView):
    def get(self, request):
        role = request.query_params.get("role", "")
        level = request.query_params.get("level", "")

        if not role:
            return Response(
                {"detail": "'role' query parameter is required."}, status=400
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    percentile_cont(0.25) WITHIN GROUP (ORDER BY cr.total_comp) AS p25,
                    percentile_cont(0.50) WITHIN GROUP (ORDER BY cr.total_comp) AS p50,
                    percentile_cont(0.75) WITHIN GROUP (ORDER BY cr.total_comp) AS p75,
                    percentile_cont(0.90) WITHIN GROUP (ORDER BY cr.total_comp) AS p90,
                    COUNT(*) AS sample_size
                FROM compensation_compensationrecord cr
                JOIN compensation_role r ON cr.role_id = r.id
                WHERE r.normalized_title ILIKE %s
                  AND (%s = '' OR cr.level ILIKE %s)
                  AND cr.total_comp IS NOT NULL
                """,
                [role, level, level],
            )
            row = cursor.fetchone()

        if not row or row[4] == 0:
            return Response(
                {"detail": "No data found for the given role and level."}, status=404
            )

        p25, p50, p75, p90, sample_size = row
        data = {
            "role": role,
            "level": level,
            "p25": float(p25) if p25 is not None else None,
            "p50": float(p50) if p50 is not None else None,
            "p75": float(p75) if p75 is not None else None,
            "p90": float(p90) if p90 is not None else None,
            "sample_size": sample_size,
        }
        serializer = CompensationSummarySerializer(data)
        return Response(serializer.data)
