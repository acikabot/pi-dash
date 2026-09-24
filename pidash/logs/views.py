"""The log viewer: pick a service, tail its log, filter it, clear it."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.core.files import clear, human_size, size_of, tail
from pidash.services.catalog import get_service, services_with

LINE_CHOICES = (100, 200, 500, 1000, 2000)


def _pick(request):
    available = services_with("log")
    wanted = request.GET.get("service") or (available[0].id if available else "")
    service = get_service(wanted)
    if service is None or not service.log:
        raise Http404("No such log")
    return service, available


def console_context(request) -> dict:
    """The console text itself — the page and the refresh partial both show it."""
    service, _available = _pick(request)
    text = tail(service.log_path, _lines(request))
    find = request.GET.get("find", "").strip()
    data = {"service": service, "text": text, "find": find}
    if find:
        kept = [line for line in text.splitlines() if find.lower() in line.lower()]
        data["text"] = "\n".join(kept)
        data["filtered"] = len(kept)
    return data


class LogsView(TemplateView):
    template_name = "logs/page.html"

    def get_context_data(self, **kwargs):
        service, available = _pick(self.request)
        kwargs.update(console_context(self.request))  # brings service, text and the filter
        return super().get_context_data(
            page_title="Logs",
            services=available,
            lines=_lines(self.request),
            line_choices=LINE_CHOICES,
            auto=self.request.GET.get("auto", "1") == "1",
            size=human_size(size_of(service.log_path)),
            **kwargs,
        )


def _lines(request) -> int:
    try:
        wanted = int(request.GET.get("lines", 200))
    except ValueError:
        wanted = 200
    return wanted if wanted in LINE_CHOICES else 200


class ConsolePartial(TemplateView):
    """Only the console text, so it can refresh on its own."""

    template_name = "logs/_console.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**console_context(self.request), **kwargs)


@require_POST
def clear_log(request, service_id: str):
    service = get_service(service_id)
    if service is None or not service.log:
        raise Http404("No such log")
    try:
        clear(service.log_path)
        messages.success(request, f"{service.name} log cleared.")
    except PermissionError:
        messages.error(request, f"Not allowed to clear {service.log_path}.")
    return redirect(request.POST.get("next") or "logs:page")
