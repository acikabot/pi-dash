"""The overview page and sign-in."""

from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from pidash.core.registry import registry


class OverviewView(TemplateView):
    """Whatever the installed modules want on the front page."""

    template_name = "core/overview.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            panels=registry.panels("overview"),
            **registry.panel_context("overview", self.request),
            **kwargs,
        )


@method_decorator(login_not_required, name="dispatch")
class SignInView(LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


@login_not_required
@require_GET
def healthz(request):
    return HttpResponse("ok", content_type="text/plain")
