import json

import pytest
from django.urls import reverse

from apps.surveys.models import SurveySubmission
from tests.surveys.factories import SurveyFactory


@pytest.mark.django_db
class TestIngestView:
    def test_successful_ingestion(self, api_client):
        survey = SurveyFactory()
        payload = {
            "survey_id": survey.pk,
            "records": [
                {
                    "role_title": "Software Engineer",
                    "location": "San Francisco, CA",
                    "total_comp": 200000,
                    "base_salary": 150000,
                    "level": "L4",
                    "years_experience": 4,
                    "company_size": "enterprise",
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
        assert SurveySubmission.objects.count() == 1

    def test_duplicate_detection(self, api_client):
        survey = SurveyFactory()
        record = {
            "role_title": "Product Manager",
            "location": "New York, NY",
            "total_comp": 180000,
        }
        payload = {"survey_id": survey.pk, "records": [record]}

        # First ingest
        r1 = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r1.status_code == 201

        # Second ingest — same record
        r2 = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r2.status_code == 200
        data = r2.json()
        assert data["submitted"] == 0
        assert data["duplicates"] == 1
        assert SurveySubmission.objects.count() == 1

    def test_missing_role_title_returns_400(self, api_client):
        survey = SurveyFactory()
        payload = {
            "survey_id": survey.pk,
            "records": [
                {
                    "location": "Austin, TX",
                    "total_comp": 150000,
                }
            ],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_survey_id_returns_400(self, api_client):
        payload = {
            "survey_id": 99999,
            "records": [{"role_title": "SWE", "total_comp": 150000}],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_negative_total_comp_returns_400(self, api_client):
        survey = SurveyFactory()
        payload = {
            "survey_id": survey.pk,
            "records": [{"role_title": "SWE", "total_comp": -1000}],
        }
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_bulk_multiple_records(self, api_client):
        survey = SurveyFactory()
        records = [
            {"role_title": f"Engineer {i}", "total_comp": 100000 + i * 10000}
            for i in range(5)
        ]
        payload = {"survey_id": survey.pk, "records": records}
        response = api_client.post(
            reverse("ingest"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["submitted"] == 5


@pytest.mark.django_db
class TestSurveyListView:
    def test_list_surveys(self, api_client):
        SurveyFactory.create_batch(3)
        response = api_client.get(reverse("survey-list"))
        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_create_survey(self, api_client):
        payload = {"name": "Levels.fyi 2024", "source": "levels", "year": 2024}
        response = api_client.post(
            reverse("survey-list"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["source"] == "levels"
