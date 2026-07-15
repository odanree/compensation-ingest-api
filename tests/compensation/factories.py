import factory

from apps.compensation.models import Location, SolarQuote, SystemConfig
from tests.surveys.factories import QuoteSubmissionFactory


class SystemConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SystemConfig

    panel_brand = factory.Sequence(lambda n: f"Panel Brand {n}")
    panel_tier_label = "Premium"
    panel_tier = "premium"
    tier_order = 2


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    raw_location = factory.Sequence(lambda n: f"City {n}, CA")
    city = factory.Sequence(lambda n: f"City {n}")
    state = "CA"
    country = "US"
    metro = "Los Angeles Metro"


class SolarQuoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SolarQuote

    submission = factory.SubFactory(QuoteSubmissionFactory)
    system_config = factory.SubFactory(SystemConfigFactory)
    location = factory.SubFactory(LocationFactory)
    system_size_band = "5-8 kW"
    system_cost = 25000
    cost_per_watt = 3.47
    installer_type = SolarQuote.InstallerType.LOCAL
