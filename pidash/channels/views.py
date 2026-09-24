"""The channel list the content bot watches, kept in its JSON config."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.core.files import read_json, write_json
from pidash.services.catalog import get_service, services_with


def _service(request=None, service_id: str | None = None):
    available = services_with("config")
    service = get_service(service_id) if service_id else (available[0] if available else None)
    if service is None or not service.config:
        raise Http404("Nothing here keeps a channel list")
    return service, available


def channels_of(service) -> list[dict]:
    data = read_json(service.config, {}) or {}
    return data.get("channels", [])


class ChannelsView(TemplateView):
    template_name = "channels/page.html"

    def get_context_data(self, **kwargs):
        service, available = _service(self.request, self.request.GET.get("service"))
        return super().get_context_data(
            page_title="Channels",
            page_subtitle=f"What {service.name} watches.",
            service=service,
            services=available,
            channels=channels_of(service),
            **kwargs,
        )


@require_POST
def add(request, service_id: str):
    service, _available = _service(request, service_id)
    channel = {
        "id": request.POST.get("id", "").strip(),
        "name": request.POST.get("name", "").strip(),
        "niche": request.POST.get("niche", "").strip(),
    }
    back = request.POST.get("next") or "channels:page"

    if not channel["id"] or not channel["name"]:
        messages.error(request, "A channel needs at least an ID and a name.")
        return redirect(back)

    data = read_json(service.config, {}) or {}
    existing = data.setdefault("channels", [])
    if any(row.get("id") == channel["id"] for row in existing):
        messages.error(request, "That channel ID is already in the list.")
        return redirect(back)

    existing.append(channel)
    try:
        write_json(service.config, data)
    except PermissionError:
        messages.error(request, f"Not allowed to write {service.config}.")
        return redirect(back)
    messages.success(request, f"Added {channel['name']}.")
    return redirect(back)


@require_POST
def remove(request, service_id: str):
    service, _available = _service(request, service_id)
    channel_id = request.POST.get("id", "")
    back = request.POST.get("next") or "channels:page"

    data = read_json(service.config, {}) or {}
    kept = [row for row in data.get("channels", []) if row.get("id") != channel_id]
    if len(kept) == len(data.get("channels", [])):
        messages.error(request, "That channel isn't in the list.")
        return redirect(back)

    data["channels"] = kept
    try:
        write_json(service.config, data)
    except PermissionError:
        messages.error(request, f"Not allowed to write {service.config}.")
        return redirect(back)
    messages.success(request, "Channel removed.")
    return redirect(back)
