# contacts/management/commands/bulk_whatsapp.py
# Usage: python manage.py bulk_whatsapp --template welcome_registration
# Filters: --category influencer --country Ghana --platform instagram

import time
from django.core.management.base import BaseCommand
from contacts.models import Contact
from contacts.services.whatsapp import send_whatsapp


class Command(BaseCommand):
    help = "Send a WhatsApp template message to a filtered segment of contacts."

    def add_arguments(self, parser):
        parser.add_argument("--template", required=True, help="Approved Meta template name")
        parser.add_argument("--category", default="",   help="Filter by category name")
        parser.add_argument("--country",  default="",   help="Filter by country")
        parser.add_argument("--platform", default="",   help="Filter by platform")
        parser.add_argument("--dry-run",  action="store_true", help="Preview count without sending")

    def handle(self, *args, **options):
        qs = Contact.objects.select_related("category").all()
        if options["category"]:
            qs = qs.filter(category__name__iexact=options["category"])
        if options["country"]:
            qs = qs.filter(country__iexact=options["country"])
        if options["platform"]:
            qs = qs.filter(platform__iexact=options["platform"])

        total = qs.count()
        self.stdout.write(f"Matched {total} contacts.")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run — no messages sent."))
            return

        if total == 0:
            self.stdout.write("Nothing to send.")
            return

        sent = failed = 0
        for contact in qs.iterator():
            success = send_whatsapp(
                to=contact.full_whatsapp,
                template=options["template"],
                params=[contact.first_name, str(contact.pk)],
                contact=contact,
            )
            if success:
                sent += 1
            else:
                failed += 1
            # Throttle: 80 messages/minute max (Meta rate limit)
            time.sleep(0.75)

        self.stdout.write(self.style.SUCCESS(f"Done. Sent: {sent}  Failed: {failed}"))
