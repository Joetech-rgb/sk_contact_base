# contacts/services/google_contacts.py
from django.conf import settings


def _get_credentials(token):
    from google.oauth2.credentials import Credentials
    return Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
        client_secret=getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
    )


def sync_contacts_to_google(token, contacts):
    try:
        from googleapiclient.discovery import build as g_build
        creds = _get_credentials(token)
        service = g_build("people", "v1", credentials=creds)
    except Exception as e:
        raise Exception(f"Could not connect to Google People API: {e}")

    synced = 0
    for contact in contacts:
        try:
            phone = getattr(contact, "full_whatsapp", "") or getattr(contact, "whatsapp_number", "") or ""
            body = {
                "names": [{"givenName": contact.full_name}],
                "phoneNumbers": [{"value": phone, "type": "mobile"}] if phone else [],
                "biographies": [{
                    "value": (
                        f"Platform: {getattr(contact, 'platform', '')}\n"
                        f"Handle: @{getattr(contact, 'handle', '') or ''}\n"
                        f"Country: {getattr(contact, 'country', '')}\n"
                        f"Source: SK Contact Base"
                    ),
                    "contentType": "TEXT_PLAIN"
                }],
            }
            email = getattr(contact, "email", None)
            if email:
                body["emailAddresses"] = [{"value": email}]
            service.people().createContact(body=body).execute()
            synced += 1
        except Exception as e:
            print(f'[Google Sync] Failed for {getattr(contact, "id", "?")}: {e}')
            continue
    return synced
