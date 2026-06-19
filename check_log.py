import django, os
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sk_contact_base.settings')
django.setup()

from contacts.models import WhatsAppLog
log = WhatsAppLog.objects.last()
print('Status:', log.status)
print('Template:', log.template)
print('Error:', log.error)
