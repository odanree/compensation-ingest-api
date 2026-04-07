import pytest
from django.test import Client

# Import and configure the Celery app so CELERY_TASK_ALWAYS_EAGER takes effect
from config.celery import app as celery_app  # noqa: F401


@pytest.fixture
def api_client():
    return Client()


@pytest.fixture
def auth_client(db):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="testuser", password="testpass")
    client = Client()
    client.force_login(user)
    return client
