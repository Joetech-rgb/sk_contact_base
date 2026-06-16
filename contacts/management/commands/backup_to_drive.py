
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Upload a full CSV backup of all contacts to Google Drive"

    def add_arguments(self, parser):
        parser.add_argument(
            "--silent", action="store_true",
            help="Suppress output (for use in cron jobs)"
        )

    def handle(self, *args, **options):
        try:
            from contacts.services.google_drive import upload_contacts_backup
            result = upload_contacts_backup()
            if not options["silent"]:
                self.stdout.write(self.style.SUCCESS(f"Backup complete: {result}"))
        except RuntimeError as e:
            self.stderr.write(self.style.ERROR(f"Backup failed: {e}"))
            raise SystemExit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))
            raise SystemExit(1)
