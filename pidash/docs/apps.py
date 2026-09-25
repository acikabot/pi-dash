from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule
from pidash.core.registry import registry


class DocsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.docs"
    label = "docs"
    verbose_name = _("Documentation")
    url_prefix = "docs/"
    description = _("The project's own documentation, rendered in the app.")

    def ready(self) -> None:
        from pidash.docs.documents import documents_for

        registry.add_panel(
            "settings",
            "docs/panels/settings.html",
            order=20,
            context=lambda request: {"documents": documents_for(request.user).values()},
        )
