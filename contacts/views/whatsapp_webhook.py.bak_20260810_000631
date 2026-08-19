import json
import os
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from contacts.models import WhatsAppLog, Contact

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "sk_webhook_secret")

import mimetypes
import requests as _requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def _download_whatsapp_media(media_id, msg_type):
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    if not media_id or not access_token:
        return ""
    try:
        meta_resp = _requests.get(
            f"https://graph.facebook.com/v19.0/{media_id}",
            headers={"Authorization": f"Bearer {access_token}"}, timeout=15,
        )
        if meta_resp.status_code != 200:
            return ""
        info = meta_resp.json()
        media_url, mime_type = info.get("url", ""), info.get("mime_type", "")
        if not media_url:
            return ""
        file_resp = _requests.get(media_url, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
        if file_resp.status_code != 200:
            return ""
        ext = mimetypes.guess_extension(mime_type) or ""
        saved_path = default_storage.save(f"whatsapp_incoming/{media_id}{ext}", ContentFile(file_resp.content))
        return default_storage.url(saved_path)
    except Exception:
        return ""




@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):

    # ── Meta verification handshake (one-time) ──────────────────
    if request.method == "GET":
        mode      = request.GET.get("hub.mode")
        token     = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("Forbidden", status=403)

    # ── Incoming message POST ───────────────────────────────────
    if request.method == "POST":
        data = json.loads(request.body)
        print(f"WEBHOOK PAYLOAD: {json.dumps(data)[:1000]}")

        try:
            entry    = data.get("entry",   [{}])[0]
            changes  = entry.get("changes",[{}])[0]
            value    = changes.get("value", {})
            messages = value.get("messages", [])
            statuses = value.get("statuses", [])

            if statuses:
                for st in statuses:
                    print(f"WEBHOOK STATUS UPDATE: {json.dumps(st)}")

            for msg in messages:
                phone        = msg.get("from", "")
                msg_type     = msg.get("type", "")
                message_text = ""
                MEDIA_TYPES  = ("image", "video", "document", "audio", "sticker")

                if msg_type == "text":
                    message_text = msg.get("text", {}).get("body", "")
                elif msg_type == "interactive":
                    # button replies
                    message_text = (
                        msg.get("interactive", {})
                           .get("button_reply", {})
                           .get("title", "")
                    )
                elif msg_type in MEDIA_TYPES:
                    media_obj = msg.get(msg_type, {})
                    message_text = media_obj.get("caption", "") or f"[{msg_type}]"
                else:
                    message_text = f"[{msg_type} message]"

                local_media_url  = ""
                local_media_type = ""
                if msg_type in MEDIA_TYPES:
                    media_id = msg.get(msg_type, {}).get("id", "")
                    local_media_url  = _download_whatsapp_media(media_id, msg_type)
                    local_media_type = msg_type

                # Try to match to an existing contact
                # strips last 9 digits for flexible matching
                contact = Contact.objects.filter(
                    whatsapp_number__endswith=phone[-9:]
                ).first()

                WhatsAppLog.objects.create(
                    contact      = contact,
                    template     = "[REPLY]",
                    phone        = phone,
                    status       = "received",
                    direction    = "in",
                    message_text = message_text,
                    media_url    = local_media_url,
                    media_type   = local_media_type,
                    is_read      = False,
                )

        except Exception as exc:
            import traceback
            print(f"WEBHOOK ERROR: {exc}")
            traceback.print_exc()

        return JsonResponse({"status": "ok"})