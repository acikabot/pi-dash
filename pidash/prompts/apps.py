from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import MenuItem, registry


class PromptsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.prompts"
    label = "prompts"
    verbose_name = _("Prompts")
    url_prefix = "prompts/"
    description = _("Edit what the bots ask the model, with their defaults kept.")

    def ready(self) -> None:
        registry.add_menu_item(
            MenuItem(key="prompts", label=_("Prompts"), url_name="prompts:page",
                     icon="chat-left-text", order=40)
        )  # fmt: skip
