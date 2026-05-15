# contacts/services/whatsapp.py
# Wraps the Meta WhatsApp Business API.
# All outbound WhatsApp messages go through send_whatsapp().
# Falls back to Africa s Talking SMS if WhatsApp fails.

import logging
import requests

from django.conf import settings

from contacts.utils import send_sms

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"


def send_whatsapp(to: str, template: str, params: list[str], contact=None) -> bool:
    """
    Send a WhatsApp template message via the Meta Graph API.

    Args:
        to:       Full international number e.g. +233241234567
        template: Approved Meta template name e.g. welcome_registration
        params:   List of parameter strings matching the template placeholders
        contact:  Contact model instance (optional, used for logging)

    Returns:
        True if WhatsApp was delivered (or SMS fallback succeeded), False otherwise.
    """
    from contacts.models import WhatsAppLog

    phone_id     = settings.WHATSAPP_PHONE_NUMBER_ID
    access_token = settings.WHATSAPP_ACCESS_TOKEN

    if not phone_id or not access_token:
        logger.warning("WhatsApp credentials not set — skipping send to %s", to)
        return False

    # Build the request payload
    components = []
    if params:
        components = [{
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in params],
        }]

    payload = {
        "messaging_product": "whatsapp",
        "to": to.replace("+", "").replace(" ", ""),
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": "en"},
            "components": components,
        },
    }

    url = GRAPH_URL.format(phone_number_id=phone_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("WhatsApp sent to %s via template %s", to, template)
        WhatsAppLog.objects.create(
            contact=contact, template=template, phone=to, status="sent"
        )
        return True

    except Exception as exc:
        logger.error("WhatsApp failed for %s: %s — trying SMS fallback", to, exc)
        WhatsAppLog.objects.create(
            contact=contact, template=template, phone=to,
            status="failed", error=str(exc)
        )
        # SMS fallback
        try:
            fallback_msg = _fallback_message(template, params, contact)
            send_sms(to, fallback_msg)
            WhatsAppLog.objects.create(
                contact=contact, template=template, phone=to, status="fallback"
            )
            logger.info("SMS fallback sent to %s", to)
            return True
        except Exception as sms_exc:
            logger.error("SMS fallback also failed for %s: %s", to, sms_exc)
            return False


def _fallback_message(template: str, params: list[str], contact) -> str:
    """Generate a plain SMS text when WhatsApp delivery fails."""
    if template == "welcome_registration" and contact:
        reg = params[1] if len(params) > 1 else str(contact.pk)
        return (
            f"Hi {contact.first_name}! Welcome to the SK Brand network! "
            f"Your registration number is #{reg}. "
            f"Save this number as S.K. Brand Links on WhatsApp. - The SK Brand Team"
        )
    # Generic fallback for any other template
    return f"SK Brand: {' '.join(params)}"
