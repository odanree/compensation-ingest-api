"""DRF throttle classes that identify clients via Cloudflare CF-Connecting-IP.

DRF's built-in SimpleRateThrottle.get_ident() reads X-Forwarded-For (or
REMOTE_ADDR as fallback), both of which are polluted by proxies:
- REMOTE_ADDR is Caddy's container IP (single value, useless as identity)
- X-Forwarded-For is Caddy's immediate upstream (a Cloudflare edge that
  varies per request, so counters bucket per-edge, not per-client)

Reading CF-Connecting-IP directly gives us the real client IP regardless
of the proxy chain shape — no NUM_PROXIES coupling, no fragile XFF
parsing. Falls back to DRF's default if the header is absent (local dev,
tests, direct-to-origin hits).
"""
from rest_framework.throttling import (
    AnonRateThrottle,
    ScopedRateThrottle,
    UserRateThrottle,
)


class _CloudflareIdentMixin:
    def get_ident(self, request):
        cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            return cf_ip
        return super().get_ident(request)


class CloudflareAnonRateThrottle(_CloudflareIdentMixin, AnonRateThrottle):
    pass


class CloudflareUserRateThrottle(_CloudflareIdentMixin, UserRateThrottle):
    pass


class CloudflareScopedRateThrottle(_CloudflareIdentMixin, ScopedRateThrottle):
    pass
