"""The system page: how the Pi is doing, bulk controls, power, and the schedule."""

from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from pidash.core.files import clear
from pidash.services import systemd
from pidash.services.catalog import services, services_with
from pidash.system import stats

POWER = {"reboot": "reboot", "shutdown": "poweroff"}
#: action, label, icon, button colour
BULK_BUTTONS = [
    ("start", "Start all", "play-fill", "success"),
    ("restart", "Restart all", "arrow-clockwise", "secondary"),
    ("stop", "Stop all", "stop-fill", "danger"),
]


class SystemView(TemplateView):
    template_name = "system/page.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            page_title="System",
            page_subtitle="The Pi itself, and everything at once.",
            tiles=stats.tiles(),
            reboot_required=stats.reboot_required(),
            bulk_buttons=BULK_BUTTONS,
            **kwargs,
        )


class TilesPartial(TemplateView):
    template_name = "system/_tiles.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(tiles=stats.tiles(), **kwargs)


class ScheduleView(TemplateView):
    template_name = "system/schedule.html"

    def get_context_data(self, **kwargs):
        known = {s.timer_unit: s for s in services() if s.timer_unit}
        rows = [
            {
                "service": known[unit],
                "next_at": row["next_at"],
                "in": row["in"],
                "last_at": row["last_at"],
                "ago": row["ago"],
            }
            for unit, row in systemd.timer_rows().items()
            if unit in known
        ]
        rows.sort(key=lambda row: row["next_at"] or systemd.now())
        return super().get_context_data(
            page_title="Schedule",
            page_subtitle="When each timed job runs next.",
            rows=rows,
            **kwargs,
        )


@require_POST
def bulk(request):
    """Start, stop or restart everything that has a control unit."""
    action = request.POST.get("action", "")
    if action not in systemd.ACTIONS:
        messages.error(request, "That action doesn't exist.")
        return redirect("system:page")

    failures = []
    for service in services():
        ok, error = systemd.control(service.control_unit, action)
        if not ok:
            failures.append(f"{service.name} ({error})")
    if failures:
        messages.error(request, "Couldn't " + action + ": " + ", ".join(failures))
    else:
        messages.success(request, f"Everything {action}ed.")
    return redirect("system:page")


@require_POST
def clear_logs(request):
    refused = []
    for service in services_with("log"):
        try:
            clear(service.log_path)
        except PermissionError:
            refused.append(service.name)
    if refused:
        messages.warning(
            request, "Cleared what I could; not allowed to clear: " + ", ".join(refused)
        )
    else:
        messages.success(request, "All logs cleared.")
    return redirect("system:page")


@require_POST
def power(request):
    action = request.POST.get("action", "")
    if action not in POWER:
        messages.error(request, "That action doesn't exist.")
        return redirect("system:page")

    ok, error = systemd.power(POWER[action])
    if ok:
        messages.success(
            request,
            "Rebooting — this page will come back in a minute."
            if action == "reboot"
            else "Shutting down — the Pi is powering off.",
        )
    else:
        messages.error(request, f"Couldn't {action}: {error}")
    return redirect("system:page")
