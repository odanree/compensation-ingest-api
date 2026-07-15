from django.apps import AppConfig


class SolarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compensation"

    def ready(self):
        # Import handlers to trigger @register_ingest_handler side effects
        # so the registry is populated before any Celery worker or view
        # dispatches through it.
        from apps.compensation import handlers  # noqa: F401
