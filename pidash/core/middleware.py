"""Security headers, mirroring the tracker's."""

from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        policy = settings.PIDASH_CONTENT_SECURITY_POLICY
        self.csp = "; ".join(f"{name} {' '.join(values)}" for name, values in policy.items())

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", self.csp)
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )
        return response
