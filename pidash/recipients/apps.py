from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class RecipientsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.recipients"
    label = "recipients"
    verbose_name = _("Settings")
    url_prefix = "settings/"
    description = _("Who receives each bot's e-mail.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="recipients", label=_("Settings"), url_name="recipients:page",
                     icon="gear", order=80)
        )  # fmt: skip
