import django, os
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sk_contact_base.settings')
django.setup()

# Patch the whatsapp service with correct token at runtime
import contacts.services.whatsapp as wa
wa.ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
wa.PHONE_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
wa.API_URL = f'https://graph.facebook.com/v19.0/{wa.PHONE_ID}/messages'

from django.utils import timezone
from contacts.models import Contact
from contacts.services.whatsapp import send_whatsapp

contact = Contact.objects.get(whatsapp_number='233530611837')
print('Contact:', contact.first_name, '| ID:', contact.pk)
print('Sending WhatsApp...')

result = send_whatsapp(
    to=contact.whatsapp_number,
    template='welcome_registration',
    params=[contact.first_name, str(contact.pk)],
    contact=contact,
)
print('WhatsApp Result:', 'SUCCESS' if result else 'FAILED')

from contacts.models import WhatsAppLog
log = WhatsAppLog.objects.last()
print('Log:', log.status, '|', log.error or 'none')
