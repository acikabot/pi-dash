from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class LogsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.logs"
    label = "logs"
    verbose_name = _("Logs")
    url_prefix = "logs/"
    description = _("Read and clear the services' log files.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="logs", label=_("Logs"), url_name="logs:page", icon="file-text", order=30)
        )
