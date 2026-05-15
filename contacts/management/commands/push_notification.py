# contacts/management/commands/push_notification.py
# Usage: python manage.py push_notification <notification_id>

from django.core.management.base import BaseCommand, CommandError
from contacts.models import Contact, Notification
from contacts.services.whatsapp import send_whatsapp
import time


class Command(BaseCommand):
    help = "Push an active notification to all contacts via WhatsApp."

    def add_arguments(self, parser):
        parser.add_argument("notification_id", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            notif = Notification.objects.get(pk=options["notification_id"], is_active=True)
        except Notification.DoesNotExist:
            raise CommandError("Notification not found or not active.")

        contacts = Contact.objects.all()
        total = contacts.count()
        self.stdout.write(f"Pushing '{notif.title}' to {total} contacts...")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run — no messages sent."))
            return

        sent = failed = 0
        for contact in contacts.iterator():
            success = send_whatsapp(
                to=contact.full_whatsapp,
                template="general_notification",
                params=[contact.first_name, notif.title, notif.body[:100]],
                contact=contact,
            )
            if success:
                sent += 1
            else:
                failed += 1
            time.sleep(0.75)

        self.stdout.write(self.style.SUCCESS(f"Done. Sent: {sent}  Failed: {failed}"))
