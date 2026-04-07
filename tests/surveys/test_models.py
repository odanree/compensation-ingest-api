import pytest

from apps.surveys.models import SurveySubmission
from tests.surveys.factories import SurveyFactory, SurveySubmissionFactory


@pytest.mark.django_db
class TestSurveyModel:
    def test_str(self):
        survey = SurveyFactory(name="Levels.fyi 2024", year=2024)
        assert str(survey) == "Levels.fyi 2024 (2024)"

    def test_unique_together_source_year(self):
        SurveyFactory(source="levels", year=2024)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            SurveyFactory(source="levels", year=2024)


@pytest.mark.django_db
class TestSurveySubmissionModel:
    def test_fingerprint_is_deterministic(self):
        data = {"role_title": "SWE", "total_comp": 200000}
        fp1 = SurveySubmission.compute_fingerprint(data)
        fp2 = SurveySubmission.compute_fingerprint(data)
        assert fp1 == fp2

    def test_fingerprint_differs_for_different_inputs(self):
        fp1 = SurveySubmission.compute_fingerprint({"role_title": "SWE"})
        fp2 = SurveySubmission.compute_fingerprint({"role_title": "PM"})
        assert fp1 != fp2

    def test_fingerprint_order_independent(self):
        fp1 = SurveySubmission.compute_fingerprint({"a": 1, "b": 2})
        fp2 = SurveySubmission.compute_fingerprint({"b": 2, "a": 1})
        assert fp1 == fp2

    def test_status_choices(self):
        assert SurveySubmission.Status.PENDING == "pending"
        assert SurveySubmission.Status.PROCESSED == "processed"
        assert SurveySubmission.Status.DUPLICATE == "duplicate"

    def test_default_status_is_pending(self):
        submission = SurveySubmissionFactory()
        assert submission.status == SurveySubmission.Status.PENDING
