
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from contacts.models import Contact, BulkMessage


class Command(BaseCommand):
    help = "Create Viewer and Sender permission groups"

    def handle(self, *args, **options):
        contact_ct     = ContentType.objects.get_for_model(Contact)
        bulk_ct        = ContentType.objects.get_for_model(BulkMessage)

        view_contact   = Permission.objects.get(codename="view_contact",    content_type=contact_ct)
        view_bulk      = Permission.objects.get(codename="view_bulkmessage", content_type=bulk_ct)
        add_bulk       = Permission.objects.get(codename="add_bulkmessage",  content_type=bulk_ct)

        viewer, _ = Group.objects.get_or_create(name="Viewer")
        viewer.permissions.set([view_contact])
        self.stdout.write("Viewer group: view contacts")

        sender, _ = Group.objects.get_or_create(name="Sender")
        sender.permissions.set([view_contact, view_bulk, add_bulk])
        self.stdout.write("Sender group: view contacts + compose/view bulk sends")

        self.stdout.write(self.style.SUCCESS("Groups ready. Assign users in /admin/auth/user/"))
