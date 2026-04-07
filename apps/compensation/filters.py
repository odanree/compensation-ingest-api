import django_filters

from apps.compensation.models import CompensationRecord


class CompensationRecordFilter(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name="role__normalized_title", lookup_expr="icontains")
    role_family = django_filters.CharFilter(field_name="role__family", lookup_expr="iexact")
    location = django_filters.CharFilter(field_name="location__metro", lookup_expr="icontains")
    city = django_filters.CharFilter(field_name="location__city", lookup_expr="icontains")
    country = django_filters.CharFilter(field_name="location__country", lookup_expr="iexact")
    level = django_filters.CharFilter(lookup_expr="iexact")
    company_size = django_filters.ChoiceFilter(choices=CompensationRecord.CompanySize.choices)
    min_total_comp = django_filters.NumberFilter(field_name="total_comp", lookup_expr="gte")
    max_total_comp = django_filters.NumberFilter(field_name="total_comp", lookup_expr="lte")
    min_years_experience = django_filters.NumberFilter(field_name="years_experience", lookup_expr="gte")
    max_years_experience = django_filters.NumberFilter(field_name="years_experience", lookup_expr="lte")

    class Meta:
        model = CompensationRecord
        fields = ["level", "company_size"]
