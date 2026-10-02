from django.http import HttpResponse

HEALTH_CHECK_PATH = "/health/"


class HealthCheckMiddleware:
    """Answer load-balancer health checks without touching ALLOWED_HOSTS, SSL redirects or the database.

    The ALB calls the task by its private IP, which would otherwise be rejected as a disallowed host.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_CHECK_PATH:
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
