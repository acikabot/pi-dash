from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class ServicesModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.services"
    label = "services"
    verbose_name = _("Services")
    url_prefix = "services/"
    description = _("The service cards, their status and their buttons.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="services", label=_("Services"), url_name="services:page",
                     icon="hdd-stack", order=20)
        )  # fmt: skip
        from pidash.services.status import all_statuses

        registry.add_panel(
            "overview",
            "services/panels/overview.html",
            order=10,
            context=lambda request: {"statuses": all_statuses(), "controls": False},
        )
        registry.add_panel("navbar", "services/panels/health_chip.html", order=10)
