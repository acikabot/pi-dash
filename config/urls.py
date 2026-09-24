"""URL routing: each enabled module is mounted at its own prefix."""

from django.apps import apps
from django.urls import include, path

from pidash.core.modules import PiDashModule

urlpatterns = [path("", include("pidash.core.urls"))]

for config in apps.get_app_configs():
    if isinstance(config, PiDashModule) and config.url_prefix and config.name != "pidash.core":
        urlpatterns.append(path(config.url_prefix, include(f"{config.name}.urls")))
