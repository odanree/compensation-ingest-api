import pytest

from tests.compensation.factories import CompensationRecordFactory, RoleFactory, LocationFactory


@pytest.mark.django_db
class TestRoleModel:
    def test_str(self):
        role = RoleFactory(normalized_title="Software Engineer")
        assert str(role) == "Software Engineer"

    def test_title_unique(self):
        RoleFactory(title="Software Engineer")
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            RoleFactory(title="Software Engineer")


@pytest.mark.django_db
class TestLocationModel:
    def test_str_with_city(self):
        loc = LocationFactory(city="San Francisco", state="CA")
        assert "San Francisco" in str(loc)

    def test_str_without_city(self):
        loc = LocationFactory(city="", state="", country="Remote")
        assert "Remote" in str(loc)


@pytest.mark.django_db
class TestCompensationRecordModel:
    def test_company_size_choices(self):
        from apps.compensation.models import CompensationRecord
        assert CompensationRecord.CompanySize.ENTERPRISE == "enterprise"
        assert CompensationRecord.CompanySize.STARTUP == "startup"

    def test_record_created(self):
        record = CompensationRecordFactory(total_comp=250000)
        assert record.total_comp == 250000
        assert record.submission is not None
