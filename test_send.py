import django, os
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sk_contact_base.settings')
import django
django.setup()

from django.utils import timezone
from contacts.models import Contact, WhatsAppLog
import requests

token = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')

print('Token length:', len(token))
print('Phone ID:', phone_id)

contact = Contact.objects.get(whatsapp_number='233540191971')
print('Contact:', contact.first_name, '| ID:', contact.pk)

url = f'https://graph.facebook.com/v19.0/{phone_id}/messages'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
}
payload = {
    'messaging_product': 'whatsapp',
    'to': contact.whatsapp_number,
    'type': 'template',
    'template': {
        'name': 'welcome_registration',
        'language': {'code': 'en_US'},
        'components': [{
            'type': 'body',
            'parameters': [
                {'type': 'text', 'text': contact.first_name},
                {'type': 'text', 'text': str(contact.pk)},
            ]
        }]
    }
}

resp = requests.post(url, json=payload, headers=headers, timeout=10)
print('Status code:', resp.status_code)
print('Response:', resp.text)
