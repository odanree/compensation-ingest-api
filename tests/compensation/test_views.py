import pytest
from django.urls import reverse

from tests.compensation.factories import CompensationRecordFactory, RoleFactory


@pytest.mark.django_db
class TestCompensationRecordListView:
    def test_list_returns_200(self, api_client):
        CompensationRecordFactory.create_batch(3)
        response = api_client.get(reverse("compensation-list"))
        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_filter_by_company_size(self, api_client):
        CompensationRecordFactory(company_size="startup")
        CompensationRecordFactory(company_size="enterprise")
        response = api_client.get(reverse("compensation-list") + "?company_size=startup")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_filter_by_level(self, api_client):
        CompensationRecordFactory(level="L4")
        CompensationRecordFactory(level="L5")
        response = api_client.get(reverse("compensation-list") + "?level=L4")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_response_has_role_and_location(self, api_client):
        CompensationRecordFactory()
        response = api_client.get(reverse("compensation-list"))
        record = response.json()["results"][0]
        assert "role" in record
        assert "location" in record
        assert "normalized_title" in record["role"]
