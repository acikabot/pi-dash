from django.utils.translation import gettext_lazy as _

from pidash.core.modules import PiDashModule


class AlertsModule(PiDashModule):
    default = True  # without this Django ignores the config (apps.py imports the base)
    name = "pidash.alerts"
    label = "alerts"
    verbose_name = _("Alerts")
    url_prefix = None  # no pages of its own; it runs on a timer
    description = _("Pushes a message when a service fails, and when it recovers.")
