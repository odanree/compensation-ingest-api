from django.db import connection
from rest_framework import generics, views
from rest_framework.response import Response

from apps.compensation.filters import SolarQuoteFilter
from apps.compensation.models import SolarQuote
from apps.compensation.serializers import CostSummarySerializer, SolarQuoteSerializer


class SolarQuoteListView(generics.ListAPIView):
    serializer_class = SolarQuoteSerializer
    filterset_class = SolarQuoteFilter
    ordering_fields = ["cost_per_watt", "system_cost", "created_at"]

    def get_queryset(self):
        return SolarQuote.objects.select_related(
            "system_config", "location", "submission__quote_source"
        ).order_by("cost_per_watt")


class CostSummaryView(views.APIView):
    def get(self, request):
        system_size_band = request.query_params.get("system_size_band", "")
        state = request.query_params.get("state", "")

        if not system_size_band and not state:
            return Response(
                {"detail": "At least one of 'system_size_band' or 'state' is required."},
                status=400,
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    percentile_cont(0.25) WITHIN GROUP (ORDER BY sq.cost_per_watt) AS p25,
                    percentile_cont(0.50) WITHIN GROUP (ORDER BY sq.cost_per_watt) AS p50,
                    percentile_cont(0.75) WITHIN GROUP (ORDER BY sq.cost_per_watt) AS p75,
                    percentile_cont(0.90) WITHIN GROUP (ORDER BY sq.cost_per_watt) AS p90,
                    COUNT(*) AS sample_size
                FROM compensation_solarquote sq
                JOIN compensation_location loc ON sq.location_id = loc.id
                WHERE (%s = '' OR sq.system_size_band ILIKE %s)
                  AND (%s = '' OR loc.state ILIKE %s)
                  AND sq.cost_per_watt IS NOT NULL
                """,
                [system_size_band, system_size_band, state, state],
            )
            row = cursor.fetchone()

        if not row or row[4] == 0:
            return Response(
                {"detail": "No data found for the given filters."}, status=404
            )

        p25, p50, p75, p90, sample_size = row
        data = {
            "system_size_band": system_size_band,
            "state": state,
            "p25": float(p25) if p25 is not None else None,
            "p50": float(p50) if p50 is not None else None,
            "p75": float(p75) if p75 is not None else None,
            "p90": float(p90) if p90 is not None else None,
            "sample_size": sample_size,
        }
        serializer = CostSummarySerializer(data)
        return Response(serializer.data)
