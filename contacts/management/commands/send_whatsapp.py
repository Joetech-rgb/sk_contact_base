from django.core.management.base import BaseCommand
from contacts.models import Contact


class Command(BaseCommand):
    help = "Send a WhatsApp template message to a single contact"

    def add_arguments(self, parser):
        parser.add_argument("contact_id", type=int, help="Contact primary key")
        parser.add_argument("template", type=str, help="Approved Meta template name")

    def handle(self, *args, **options):
        try:
            contact = Contact.objects.get(pk=options["contact_id"])
        except Contact.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"No contact with ID {options['contact_id']}"))
            return

        from contacts.services.whatsapp import send_whatsapp
        ok = send_whatsapp(
            to=contact.full_whatsapp,
            template=options["template"],
            params=[contact.first_name, str(contact.pk)],
            contact=contact,
        )
        if ok:
            self.stdout.write(self.style.SUCCESS(f"Sent {options['template']} to {contact.full_name} ({contact.full_whatsapp})"))
        else:
            self.stderr.write(self.style.ERROR(f"Failed — check WhatsAppLog in admin for details"))
