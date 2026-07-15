import pytest

from apps.surveys.models import QuoteSubmission
from tests.surveys.factories import QuoteSourceFactory, QuoteSubmissionFactory


@pytest.mark.django_db
class TestQuoteSourceModel:
    def test_str(self):
        source = QuoteSourceFactory(name="SunRun 2024", quote_year=2024)
        assert str(source) == "SunRun 2024 (2024)"

    def test_unique_together_installer_year(self):
        QuoteSourceFactory(installer_name="sunrun", quote_year=2024)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            QuoteSourceFactory(installer_name="sunrun", quote_year=2024)


@pytest.mark.django_db
class TestQuoteSubmissionModel:
    def test_fingerprint_is_deterministic(self):
        data = {"panel_brand": "LG", "system_cost": 25000}
        fp1 = QuoteSubmission.compute_fingerprint(data)
        fp2 = QuoteSubmission.compute_fingerprint(data)
        assert fp1 == fp2

    def test_fingerprint_differs_for_different_inputs(self):
        fp1 = QuoteSubmission.compute_fingerprint({"panel_brand": "LG"})
        fp2 = QuoteSubmission.compute_fingerprint({"panel_brand": "SunPower"})
        assert fp1 != fp2

    def test_fingerprint_order_independent(self):
        fp1 = QuoteSubmission.compute_fingerprint({"a": 1, "b": 2})
        fp2 = QuoteSubmission.compute_fingerprint({"b": 2, "a": 1})
        assert fp1 == fp2

    def test_status_choices(self):
        assert QuoteSubmission.Status.PENDING == "pending"
        assert QuoteSubmission.Status.PROCESSED == "processed"
        assert QuoteSubmission.Status.DUPLICATE == "duplicate"

    def test_default_status_is_pending(self):
        submission = QuoteSubmissionFactory()
        assert submission.status == QuoteSubmission.Status.PENDING
