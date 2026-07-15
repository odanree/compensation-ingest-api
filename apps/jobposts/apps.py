from django.apps import AppConfig


class JobpostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobposts"

    def ready(self):
        # Register the "job_post" handler with the shared ingest registry.
        from apps.jobposts import handlers  # noqa: F401
