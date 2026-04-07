import factory

from apps.surveys.models import Survey, SurveySubmission


class SurveyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Survey

    name = factory.Sequence(lambda n: f"Survey {n}")
    source = factory.Sequence(lambda n: f"source-{n}")
    year = 2024


class SurveySubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SurveySubmission

    survey = factory.SubFactory(SurveyFactory)
    raw_data = factory.LazyAttributeSequence(
        lambda o, n: {
            "role_title": f"Software Engineer {n}",
            "location": "San Francisco, CA",
            "base_salary": 150000,
            "total_comp": 220000 + n,
            "level": "L4",
            "years_experience": 5,
            "company_size": "enterprise",
        }
    )
    fingerprint = factory.LazyAttribute(
        lambda o: SurveySubmission.compute_fingerprint(o.raw_data)
    )
