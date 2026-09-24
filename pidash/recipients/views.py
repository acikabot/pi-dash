"""The settings page: who receives each bot's e-mail."""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.recipients import store
from pidash.services.catalog import get_service, services_with


class RecipientsView(TemplateView):
    template_name = "recipients/page.html"

    def get_context_data(self, **kwargs):
        current = store.all_recipients()
        rows = [
            {"service": service, "addresses": current.get(service.id, "")}
            for service in services_with("email")
        ]
        return super().get_context_data(
            page_title="Settings",
            page_subtitle="Where each bot sends its e-mail.",
            rows=rows,
            store_path=store.path(),
            **kwargs,
        )


@require_POST
def save(request, service_id: str):
    service = get_service(service_id)
    if service is None or not service.email:
        raise Http404("That service doesn't send e-mail")
    try:
        store.set_for(service.id, request.POST.get("addresses", ""))
    except PermissionError:
        messages.error(request, f"Not allowed to write {store.path()}.")
        return redirect("recipients:page")

    note = " Restart it to pick this up." if service.kind == "resident" else ""
    messages.success(request, f"Recipients saved for {service.name}.{note}")
    return redirect("recipients:page")
