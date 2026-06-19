import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sk_contact_base.settings')
django.setup()

from contacts.models import Contact
fields = [f.name for f in Contact._meta.get_fields()]
print('Contact fields:')
for f in fields:
    print(' -', f)
