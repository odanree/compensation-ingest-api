import django_filters

from apps.surveys.models import Survey, SurveySubmission


class SurveyFilter(django_filters.FilterSet):
    year = django_filters.NumberFilter()
    source = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Survey
        fields = ["year", "source"]


class SurveySubmissionFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=SurveySubmission.Status.choices)
    survey = django_filters.NumberFilter(field_name="survey_id")

    class Meta:
        model = SurveySubmission
        fields = ["status", "survey"]
