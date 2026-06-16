# contacts/services/whatsapp.py
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
load_dotenv()
from django.utils import timezone
from contacts.models import WhatsAppLog

PHONE_ID     = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
API_URL      = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

# Session with built-in retry + connection pooling — reused across all sends
_session = requests.Session()
_retry = Retry(
    total=3,
    backoff_factor=1,          # waits 1s, 2s, 4s between retries
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"],
    raise_on_status=False,
)
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=5, pool_maxsize=10)
_session.mount("https://", _adapter)
_session.mount("http://",  _adapter)


def send_whatsapp(to: str, template: str, params: list, contact=None, footer: str = "", language: str = "en") -> bool:
    if not PHONE_ID or not ACCESS_TOKEN:
        _log(contact, template, "failed", "Missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN")
        return False

    all_params = list(params)
    if footer:
        all_params.append(footer)

    components = []
    if all_params:
        components = [{
            "type": "body",
            "parameters": [{"type": "text", "text": str(p)} for p in all_params],
        }]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": language},
            "components": components,
        },
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        resp = _session.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=(5, 20),   # (connect timeout, read timeout)
        )
        if resp.status_code == 200:
            _log(contact, template, "sent", "")
            return True
        else:
            _log(contact, template, "failed", resp.text[:500])
            return False
    except requests.exceptions.Timeout as exc:
        _log(contact, template, "failed", f"Timeout: {str(exc)[:300]}")
        return False
    except requests.exceptions.ConnectionError as exc:
        _log(contact, template, "failed", f"ConnectionError: {str(exc)[:300]}")
        return False
    except Exception as exc:
        _log(contact, template, "failed", str(exc)[:500])
        return False


def _log(contact, template, status, error):
    try:
        WhatsAppLog.objects.create(
            contact=contact,
            template=template,
            status=status,
            error=error,
            timestamp=timezone.now(),
        )
    except Exception:
        pass