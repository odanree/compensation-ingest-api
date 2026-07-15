from .base import *  # noqa: F401, F403
import environ

env = environ.Env()

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

SECURE_SSL_REDIRECT = True
# Caddy terminates TLS and forwards HTTP internally; trust its X-Forwarded-Proto
# so is_secure() returns True and SECURE_SSL_REDIRECT doesn't loop.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Shared Redis cache — required for DRF throttling under multi-worker gunicorn.
# LocMemCache (Django's default) is per-process, so each worker would keep its
# own rate-limit counters and the effective ceiling would be N_workers × rate.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "KEY_PREFIX": "solar_ingest",
    },
}
