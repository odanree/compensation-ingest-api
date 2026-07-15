import django_filters

from apps.compensation.models import SolarQuote


class SolarQuoteFilter(django_filters.FilterSet):
    panel_tier = django_filters.CharFilter(
        field_name="system_config__panel_tier", lookup_expr="iexact"
    )
    state = django_filters.CharFilter(field_name="location__state", lookup_expr="icontains")
    city = django_filters.CharFilter(field_name="location__city", lookup_expr="icontains")
    metro = django_filters.CharFilter(field_name="location__metro", lookup_expr="icontains")
    system_size_band = django_filters.CharFilter(lookup_expr="iexact")
    installer_type = django_filters.ChoiceFilter(choices=SolarQuote.InstallerType.choices)
    min_cost_per_watt = django_filters.NumberFilter(field_name="cost_per_watt", lookup_expr="gte")
    max_cost_per_watt = django_filters.NumberFilter(field_name="cost_per_watt", lookup_expr="lte")
    min_system_cost = django_filters.NumberFilter(field_name="system_cost", lookup_expr="gte")
    max_system_cost = django_filters.NumberFilter(field_name="system_cost", lookup_expr="lte")

    class Meta:
        model = SolarQuote
        fields = ["system_size_band", "installer_type"]
