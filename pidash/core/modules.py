"""Base class for a dashboard module.

A module is a normal Django app whose config subclasses this. It registers its menu
entries and buttons in ``ready()``.

Trap: an app config that lives in a module which also imports this base is only used by
Django when it sets ``default = True``. Every module's apps.py does.
"""

from django.apps import AppConfig


class PiDashModule(AppConfig):
    #: Mounted under this URL prefix; None means the module has no pages.
    url_prefix: str | None = None
    #: Shown in Settings → Modules.
    description: str = ""

    def ready(self) -> None:  # pragma: no cover - overridden by each module
        pass
