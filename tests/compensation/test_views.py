import pytest
from django.urls import reverse

from tests.compensation.factories import LocationFactory, SolarQuoteFactory, SystemConfigFactory


@pytest.mark.django_db
class TestSolarQuoteListView:
    def test_list_returns_200(self, api_client):
        SolarQuoteFactory.create_batch(3)
        response = api_client.get(reverse("solar-quote-list"))
        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_filter_by_panel_tier(self, api_client):
        premium_config = SystemConfigFactory(panel_tier="premium")
        standard_config = SystemConfigFactory(panel_tier="standard")
        SolarQuoteFactory(system_config=premium_config)
        SolarQuoteFactory(system_config=standard_config)
        response = api_client.get(reverse("solar-quote-list") + "?panel_tier=premium")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_filter_by_system_size_band(self, api_client):
        SolarQuoteFactory(system_size_band="5-8 kW")
        SolarQuoteFactory(system_size_band="8-12 kW")
        response = api_client.get(reverse("solar-quote-list") + "?system_size_band=5-8+kW")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_response_has_system_config_and_location(self, api_client):
        SolarQuoteFactory()
        response = api_client.get(reverse("solar-quote-list"))
        record = response.json()["results"][0]
        assert "system_config" in record
        assert "location" in record
        assert "cost_per_watt" in record


@pytest.mark.django_db
class TestCostSummaryView:
    def test_requires_filter_param(self, api_client):
        response = api_client.get(reverse("cost-summary"))
        assert response.status_code == 400

    def test_no_data_returns_404(self, api_client):
        response = api_client.get(reverse("cost-summary") + "?state=TX")
        assert response.status_code == 404

    def test_returns_percentiles_by_state(self, api_client):
        loc = LocationFactory(state="CA")
        for cpw in [2.8, 3.2, 3.5, 3.8, 4.1]:
            SolarQuoteFactory(location=loc, cost_per_watt=cpw)
        response = api_client.get(reverse("cost-summary") + "?state=CA")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "CA"
        assert data["sample_size"] == 5
        assert data["p50"] is not None
