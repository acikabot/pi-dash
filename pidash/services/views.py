"""Service cards and the buttons on them."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.services import systemd
from pidash.services.catalog import get_service
from pidash.services.status import all_statuses


class ServicesView(TemplateView):
    template_name = "services/page.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            page_title="Services",
            page_subtitle="Everything this Pi runs.",
            statuses=all_statuses(),
            controls=True,
            **kwargs,
        )


class CardsPartial(TemplateView):
    """Just the cards — HTMX re-fetches this every few seconds."""

    template_name = "services/_cards.html"

    def get_context_data(self, **kwargs):
        controls = self.request.GET.get("controls") == "1"
        return super().get_context_data(statuses=all_statuses(), controls=controls, **kwargs)


class HealthChip(TemplateView):
    """The navbar chip: everything fine, or how many services need a look."""

    template_name = "services/_health_chip.html"

    def get_context_data(self, **kwargs):
        problems = sum(1 for status in all_statuses() if status.is_problem)
        return super().get_context_data(problems=problems, **kwargs)


def _service_or_404(service_id: str):
    service = get_service(service_id)
    if service is None:
        raise Http404(f"No service called {service_id!r}")
    return service


@require_POST
def control(request, service_id: str):
    """Start, stop or restart a service (its timer, when it is a scheduled one)."""
    service = _service_or_404(service_id)
    action = request.POST.get("action", "")
    if action not in systemd.ACTIONS:
        messages.error(request, "That action doesn't exist.")
        return redirect(request.POST.get("next") or "services:page")

    ok, error = systemd.control(service.control_unit, action)
    if ok:
        messages.success(request, f"{service.name} {action}ed.")
    else:
        messages.error(request, f"Couldn't {action} {service.name}: {error}")
    return redirect(request.POST.get("next") or "services:page")


@require_POST
def run(request, service_id: str):
    """Fire a manual run through systemd, so it runs as the right user."""
    service = _service_or_404(service_id)
    mode = request.POST.get("mode", "")
    if not service.has_run(mode):
        messages.error(request, "That run doesn't exist for this service.")
        return redirect(request.POST.get("next") or "services:page")

    label = next(r.label for r in service.runs if r.mode == mode)
    ok, error = systemd.start_unit(service.run_unit(mode))
    if ok:
        messages.success(request, f"{label} started — watch the log for output.")
    else:
        messages.error(request, f"Couldn't start {label}: {error}")
    return redirect(request.POST.get("next") or "services:page")
