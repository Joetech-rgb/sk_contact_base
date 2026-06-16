import json,time,threading
import requests as _requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .permissions import require_group
from django.http import JsonResponse
from django.shortcuts import redirect, render
from ..models import BulkMessage, Contact, ServiceRequest

_bulk_send_lock = threading.Lock()

def _send_with_retry(contact, template, extra_params, retries=3, delay=8, language=None):
    from ..services.whatsapp import send_whatsapp
    for attempt in range(1, retries + 1):
        try:
            params = extra_params if extra_params else [contact.first_name]
            lang = language or ("en_US" if template == "sk_welcome" else "en")
            result = send_whatsapp(to=contact.full_whatsapp, template=template, params=params, contact=contact, language=lang)
            if result:
                return True
            print(f"[Bulk Send] API rejection for {contact.full_whatsapp} — not retrying.")
            return False
        except (_requests.exceptions.ConnectionError, _requests.exceptions.Timeout) as exc:
            print(f"[Bulk Send] Network error for {contact.full_whatsapp} — attempt {attempt}/{retries}: {exc}")
            if attempt < retries:
                time.sleep(delay)
    print(f"[Bulk Send] Gave up on {contact.full_whatsapp} after {retries} attempts.")
    return False
