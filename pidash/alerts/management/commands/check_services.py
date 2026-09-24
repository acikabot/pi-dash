"""Look at every service and push a message when one breaks (or comes back).

Run on a timer: `python manage.py check_services`. Nothing is sent while everything is
fine, and a service that stays broken is reported once, not every five minutes.
"""

from django.core.management.base import BaseCommand

from pidash.alerts.models import ServiceAlert
from pidash.alerts.notify import send
from pidash.services.status import all_statuses


class Command(BaseCommand):
    help = "Notify about services that are failing, and about ones that recovered."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quiet", action="store_true", help="Check and record, but send nothing."
        )

    def handle(self, *args, quiet=False, **options):
        known = {alert.service_id: alert for alert in ServiceAlert.objects.all()}
        problems = []

        for status in all_statuses():
            service_id = status.service.id
            if status.is_problem:
                if service_id not in known:
                    alert = ServiceAlert.objects.create(service_id=service_id, label=status.label)
                    sent = (
                        False
                        if quiet
                        else send(
                            f"{status.service.name}: {status.label}",
                            f"{status.service.name} on this Pi is {status.label.lower()}.",
                            priority="high",
                            tags="warning",
                        )
                    )
                    ServiceAlert.objects.filter(pk=alert.pk).update(notified=sent)
                    problems.append(f"{service_id} ({status.label})")
            elif service_id in known:
                alert = known[service_id]
                was_notified = alert.notified
                alert.delete()
                if not quiet and was_notified:
                    send(
                        f"{status.service.name}: back to normal",
                        f"{status.service.name} is {status.label.lower()} again.",
                        tags="white_check_mark",
                    )
                problems.append(f"{service_id} recovered")

        self.stdout.write(", ".join(problems) if problems else "Nothing to report.")
