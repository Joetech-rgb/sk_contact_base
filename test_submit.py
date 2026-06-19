from django.test import Client
from contacts.models import Contact

c = Client()

contacts = [
    {'first_name':'Ama','surname':'Mensah','email':'ama.mensah@test.com','whatsapp_number':'+233241000001','whatsapp_dial_code':'+233','country':'Ghana','agree_to_terms':'on'},
    {'first_name':'Kofi','surname':'Asante','email':'kofi.asante@test.com','whatsapp_number':'+233241000002','whatsapp_dial_code':'+233','country':'Ghana','agree_to_terms':'on'},
    {'first_name':'Abena','surname':'Osei','email':'abena.osei@test.com','whatsapp_number':'+233241000003','whatsapp_dial_code':'+233','country':'Ghana','agree_to_terms':'on'},
    {'first_name':'Kwame','surname':'Boateng','email':'kwame.boateng@test.com','whatsapp_number':'+233241000004','whatsapp_dial_code':'+233','country':'Ghana','agree_to_terms':'on'},
    {'first_name':'Akua','surname':'Darko','email':'akua.darko@test.com','whatsapp_number':'+233241000005','whatsapp_dial_code':'+233','country':'Ghana','agree_to_terms':'on'},
]

before = Contact.objects.count()
print('Contacts before:', before)

for p in contacts:
    r = c.post('/', data=p, follow=False)
    status = 'SAVED' if r.status_code == 302 else 'FAILED'
    print(p['first_name'] + ': status=' + str(r.status_code) + ' -> ' + status)
    if r.status_code == 200:
        from contacts.forms import ContactForm
        form = ContactForm(p)
        form.is_valid()
        print('  Errors: ' + str(form.errors))

print('Contacts after:', Contact.objects.count())
print('New contacts added:', str(Contact.objects.count() - before))
