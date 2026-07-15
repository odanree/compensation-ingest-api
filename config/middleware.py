class CloudflareRealIPMiddleware:
    """Normalize client identity behind Cloudflare + Caddy.

    Behind CF, REMOTE_ADDR is Caddy's container IP and X-Forwarded-For
    holds the immediate CF edge (which varies per request). Neither
    identifies the real client. This middleware:

    - Rewrites REMOTE_ADDR to the value from CF-Connecting-IP, so any
      code path that inspects REMOTE_ADDR (Django admin audit, custom
      views, access logs) sees the real client IP.
    - Prepends the real client IP to X-Forwarded-For, preserving the
      existing chain, so log-shippers and tracing tools see the proper
      "<real-client>, <cf-edge>" hop sequence.

    Rate-limit identity is handled separately by config.throttles.* —
    those read CF-Connecting-IP directly and are not affected by XFF
    parsing quirks (which is why we can preserve the XFF chain here
    without breaking throttling).

    Only trust CF-Connecting-IP when the immediate upstream is expected
    to be Cloudflare. Direct hits to the origin IP bypassing CF could
    spoof the header; in this deployment CF fronts every route by
    orange-cloud DNS and Caddy only listens on the CF-issued cert.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        real_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if real_ip:
            request.META["REMOTE_ADDR"] = real_ip
            existing_xff = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
            if existing_xff:
                request.META["HTTP_X_FORWARDED_FOR"] = f"{real_ip}, {existing_xff}"
            else:
                request.META["HTTP_X_FORWARDED_FOR"] = real_ip
        return self.get_response(request)
