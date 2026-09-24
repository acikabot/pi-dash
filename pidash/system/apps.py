from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class SystemModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.system"
    label = "system"
    verbose_name = _("System")
    url_prefix = "system/"
    description = _("The Pi's own health, bulk controls, the schedule and power.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="schedule", label=_("Schedule"), url_name="system:schedule",
                     icon="calendar3", order=60)
        )  # fmt: skip
        registry.add_menu_item(
            MenuItem(key="system", label=_("System"), url_name="system:page",
                     icon="cpu", order=70)
        )  # fmt: skip
        from pidash.system.stats import tiles

        registry.add_panel(
            "overview", "system/panels/tiles.html", order=20,
            context=lambda request: {"tiles": tiles()},
        )  # fmt: skip
