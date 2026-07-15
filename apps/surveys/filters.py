import django_filters

from apps.surveys.models import QuoteSource, QuoteSubmission


class QuoteSourceFilter(django_filters.FilterSet):
    quote_year = django_filters.NumberFilter()
    installer_name = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = QuoteSource
        fields = ["quote_year", "installer_name"]


class QuoteSubmissionFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=QuoteSubmission.Status.choices)
    quote_source = django_filters.NumberFilter(field_name="quote_source_id")

    class Meta:
        model = QuoteSubmission
        fields = ["status", "quote_source"]
