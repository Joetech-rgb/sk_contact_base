import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sk_contact_base.settings')
django.setup()

from contacts.models import Contact
print('Field details:')
for f in Contact._meta.get_fields():
    try:
        blank = getattr(f, 'blank', '?')
        null = getattr(f, 'null', '?')
        default = getattr(f, 'default', '?')
        ftype = type(f).__name__
        print(f'  {f.name}: {ftype} | blank={blank} | null={null} | default={default}')
    except:
        print(f'  {f.name}: (relation)')
