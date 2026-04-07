import pytest


@pytest.fixture(autouse=True)
def reset_sequences(django_db_reset_sequences):
    pass
