from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class CoreModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.core"
    label = "core"
    verbose_name = _("Core")
    url_prefix = ""
    description = _("Layout, navigation, sign-in and the overview page.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="overview", label=_("Overview"), url_name="core:overview",
                     icon="speedometer2", order=10)
        )  # fmt: skip
