# contacts/management/commands/send_whatsapp.py
# Usage: python manage.py send_whatsapp <contact_id> <template>
# Example: python manage.py send_whatsapp 42 welcome_registration

from django.core.management.base import BaseCommand, CommandError
from contacts.models import Contact
from contacts.services.whatsapp import send_whatsapp


class Command(BaseCommand):
    help = "Send a WhatsApp template message to a single contact by ID."

    def add_arguments(self, parser):
        parser.add_argument("contact_id", type=int, help="Contact primary key")
        parser.add_argument("template",   type=str, help="Approved Meta template name")

    def handle(self, *args, **options):
        try:
            contact = Contact.objects.get(pk=options["contact_id"])
        except Contact.DoesNotExist:
            raise CommandError(f"Contact {options['contact_id']} not found.")

        template = options["template"]
        self.stdout.write(f"Sending {template} to {contact.full_name} ({contact.full_whatsapp})...")

        success = send_whatsapp(
            to=contact.full_whatsapp,
            template=template,
            params=[contact.first_name, str(contact.pk)],
            contact=contact,
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f"Sent successfully to {contact.full_whatsapp}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed — check WhatsAppLog in admin"))
