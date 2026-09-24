"""Print the files and folders the dashboard needs to reach, from the catalogue.

deploy/install.sh loops over this to set the group and the ACLs, so adding a service to
config/services.py is all it takes — the installer never needs editing.
"""

from django.core.management.base import BaseCommand

from pidash.services.catalog import services


class Command(BaseCommand):
    help = "List paths the dashboard reads or writes, as 'kind<TAB>path' lines."

    def handle(self, *args, **options):
        for service in services():
            self.stdout.write(f"dir\t{service.dir}")
            if service.log:
                self.stdout.write(f"log\t{service.log_path}")
            if service.prompts:
                self.stdout.write(f"prompts\t{service.prompts_dir}")
            if service.config:
                self.stdout.write(f"config\t{service.config}")
