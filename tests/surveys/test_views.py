import json

import pytest
from django.urls import reverse

from apps.surveys.models import QuoteSubmission
from tests.surveys.factories import QuoteSourceFactory


@pytest.mark.django_db
class TestIngestView:
    def test_successful_ingestion(self, api_client):
        source = QuoteSourceFactory()
        payload = {
            "quote_source_id": source.pk,
            "records": [
                {
                    "panel_brand": "LG NeON 2",
                    "location": "San Diego, CA",
                    "system_size_kw": 7.2,
                    "system_cost": 25000,
                    "installer_type": "local",
                }
            ],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["submitted"] == 1
        assert data["duplicates"] == 0
        assert QuoteSubmission.objects.count() == 1

    def test_duplicate_detection(self, api_client):
        source = QuoteSourceFactory()
        record = {
            "panel_brand": "SunPower Maxeon",
            "location": "Phoenix, AZ",
            "system_cost": 30000,
            "cost_per_watt": 3.2,
        }
        payload = {"quote_source_id": source.pk, "records": [record]}

        r1 = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r1.status_code == 201

        r2 = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["submitted"] == 0
        assert data["duplicates"] == 1
        assert QuoteSubmission.objects.count() == 1

    def test_missing_cost_fields_returns_400(self, api_client):
        source = QuoteSourceFactory()
        payload = {
            "quote_source_id": source.pk,
            "records": [
                {
                    "panel_brand": "LONGi",
                    "location": "Austin, TX",
                    # no system_cost or cost_per_watt
                }
            ],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_quote_source_returns_400(self, api_client):
        payload = {
            "quote_source_id": 99999,
            "records": [{"panel_brand": "LG", "system_cost": 20000}],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bulk_multiple_records(self, api_client):
        source = QuoteSourceFactory()
        records = [
            {"panel_brand": f"Brand {i}", "system_cost": 20000 + i * 1000, "cost_per_watt": 3.0 + i * 0.1}
            for i in range(5)
        ]
        payload = {"quote_source_id": source.pk, "records": records}
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["submitted"] == 5


@pytest.mark.django_db
class TestQuoteSourceListView:
    def test_list_quote_sources(self, api_client):
        QuoteSourceFactory.create_batch(3)
        response = api_client.get(reverse("quote-source-list"))
        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_create_quote_source(self, auth_client):
        payload = {
            "name": "SunRun CA 2024",
            "installer_name": "sunrun",
            "quote_year": 2024,
        }
        response = auth_client.post(
            reverse("quote-source-list"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["installer_name"] == "sunrun"
