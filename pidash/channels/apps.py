from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class ChannelsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.channels"
    label = "channels"
    verbose_name = _("Channels")
    url_prefix = "channels/"
    description = _("The channel list the content bot watches.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="channels", label=_("Channels"), url_name="channels:page",
                     icon="broadcast", order=50)
        )  # fmt: skip
