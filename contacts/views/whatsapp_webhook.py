import json
import os
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from contacts.models import WhatsAppLog, Contact

VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "sk_webhook_secret")


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

                if msg_type == "text":
                    message_text = msg.get("text", {}).get("body", "")
                elif msg_type == "interactive":
                    # button replies
                    message_text = (
                        msg.get("interactive", {})
                           .get("button_reply", {})
                           .get("title", "")
                    )
                else:
                    message_text = f"[{msg_type} message]"

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
                )

        except Exception as exc:
            import traceback
            print(f"WEBHOOK ERROR: {exc}")
            traceback.print_exc()

        return JsonResponse({"status": "ok"})