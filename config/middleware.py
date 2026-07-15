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
        # DIAG (temporary): log what we actually see for one round of throttle testing.
        print(
            f"[cf-diag] path={request.path} "
            f"REMOTE_ADDR={request.META.get('REMOTE_ADDR')} "
            f"CF_CIP={real_ip} "
            f"XFF={request.META.get('HTTP_X_FORWARDED_FOR')} "
            f"XRIP={request.META.get('HTTP_X_REAL_IP')}",
            flush=True,
        )
        if real_ip:
            request.META["REMOTE_ADDR"] = real_ip
        return self.get_response(request)
