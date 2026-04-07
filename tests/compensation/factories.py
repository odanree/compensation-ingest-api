import factory

from apps.compensation.models import CompensationRecord, Location, Role
from tests.surveys.factories import SurveySubmissionFactory


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    title = factory.Sequence(lambda n: f"Software Engineer {n}")
    normalized_title = factory.LazyAttribute(lambda o: o.title)
    family = "Engineering"


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    raw_location = factory.Sequence(lambda n: f"City {n}, CA")
    city = factory.Sequence(lambda n: f"City {n}")
    state = "CA"
    country = "US"
    metro = "San Francisco Bay Area"


class CompensationRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CompensationRecord

    submission = factory.SubFactory(SurveySubmissionFactory)
    role = factory.SubFactory(RoleFactory)
    location = factory.SubFactory(LocationFactory)
    level = "L4"
    base_salary = 150000
    total_comp = 220000
    years_experience = 5
    company_size = CompensationRecord.CompanySize.ENTERPRISE
