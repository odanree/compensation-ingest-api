import factory

from apps.surveys.models import QuoteSource, QuoteSubmission


class QuoteSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuoteSource

    name = factory.Sequence(lambda n: f"Quote Source {n}")
    installer_name = factory.Sequence(lambda n: f"installer-{n}")
    quote_year = 2024


class QuoteSubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuoteSubmission

    quote_source = factory.SubFactory(QuoteSourceFactory)
    raw_data = factory.LazyAttributeSequence(
        lambda o, n: {
            "panel_brand": "LG NeON 2",
            "location": "San Diego, CA",
            "system_size_kw": 7.2 + n * 0.1,
            "system_cost": 25000 + n * 500,
            "installer_type": "local",
        }
    )
    fingerprint = factory.LazyAttribute(
        lambda o: QuoteSubmission.compute_fingerprint(o.raw_data)
    )
