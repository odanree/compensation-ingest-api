import pytest

from tests.compensation.factories import LocationFactory, SolarQuoteFactory, SystemConfigFactory


@pytest.mark.django_db
class TestSystemConfigModel:
    def test_str(self):
        config = SystemConfigFactory(panel_tier_label="LG Premium")
        assert str(config) == "LG Premium"

    def test_panel_brand_unique(self):
        SystemConfigFactory(panel_brand="LG NeON 2")
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            SystemConfigFactory(panel_brand="LG NeON 2")


@pytest.mark.django_db
class TestLocationModel:
    def test_str_with_city(self):
        loc = LocationFactory(city="San Diego", state="CA")
        assert "San Diego" in str(loc)

    def test_str_without_city(self):
        loc = LocationFactory(city="", state="", country="Remote")
        assert "Remote" in str(loc)


@pytest.mark.django_db
class TestSolarQuoteModel:
    def test_installer_type_choices(self):
        from apps.compensation.models import SolarQuote

        assert SolarQuote.InstallerType.LOCAL == "local"
        assert SolarQuote.InstallerType.NATIONAL == "national"

    def test_quote_created(self):
        quote = SolarQuoteFactory(cost_per_watt=3.47)
        assert float(quote.cost_per_watt) == 3.47
        assert quote.submission is not None
