class CloudflareRealIPMiddleware:
    """Trust Cloudflare's CF-Connecting-IP header as the true client IP.

    Behind Cloudflare, REMOTE_ADDR is the CF edge server and each request
    can land on a different edge — DRF's per-IP throttling then buckets
    per-edge instead of per-client, defeating the rate limit. This rewrites
    REMOTE_ADDR to the value in CF-Connecting-IP so downstream code (DRF
    throttles, access logs) sees the real client IP.

    Only trust the header when the immediate upstream is expected to be
    Cloudflare — direct hits to the origin IP bypassing CF could otherwise
    spoof it. In this deployment Caddy is fronted by Cloudflare-orange-cloud
    DNS and rate-limit accuracy matters more than spoof resistance for a
    portfolio demo.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        real_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if real_ip:
            request.META["REMOTE_ADDR"] = real_ip
            # DRF's SimpleRateThrottle.get_ident() reads X-Forwarded-For in
            # preference to REMOTE_ADDR. Caddy sets XFF to the immediate
            # upstream (a Cloudflare edge, different per request), which
            # defeats per-client throttling. Overwrite XFF to the real client
            # IP so downstream code — DRF throttles, access logs, geoblocks —
            # all agree on identity.
            request.META["HTTP_X_FORWARDED_FOR"] = real_ip
        return self.get_response(request)
