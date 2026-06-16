
import csv
import io
import datetime
from django.utils import timezone


def _get_credentials():
    from contacts.models import GoogleToken
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from django.conf import settings

    token = GoogleToken.objects.order_by("-id").first()
    if not token:
        raise RuntimeError("No Google account connected. Connect one via the dashboard.")

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.access_token = creds.token
        token.set_expiry(creds.expiry)
        token.save()
    return creds


def _get_or_create_folder(service, folder_name="SK Contact Base Backups"):
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _build_csv():
    from contacts.models import Contact
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "First Name", "Surname", "Email", "WhatsApp",
        "Country", "Platform", "Handle", "Follower Range",
        "Category", "Age Range", "Region", "Referral Source", "Date Added",
    ])
    for c in Contact.objects.select_related("category", "referral_source").order_by("id"):
        writer.writerow([
            c.id, c.first_name, c.surname, c.email or "",
            c.full_whatsapp, c.country, c.platform or "",
            c.handle_clean or "", c.get_follower_range_display() if c.follower_range else "",
            str(c.category) if c.category else "",
            c.age_range or "", getattr(c, "region", "") or "",
            str(c.referral_source) if c.referral_source else "",
            c.date_added.strftime("%Y-%m-%d %H:%M"),
        ])
    return output.getvalue()


def upload_contacts_backup():
    from googleapiclient.discovery import build as g_build
    from googleapiclient.http import MediaInMemoryUpload

    creds   = _get_credentials()
    service = g_build("drive", "v3", credentials=creds)

    folder_id = _get_or_create_folder(service)
    csv_data  = _build_csv().encode("utf-8")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename  = f"sk_contacts_backup_{timestamp}.csv"

    media = MediaInMemoryUpload(csv_data, mimetype="text/csv", resumable=False)
    file_meta = {"name": filename, "parents": [folder_id]}
    uploaded  = service.files().create(body=file_meta, media_body=media, fields="id,name").execute()

    from contacts.models import Contact
    total = Contact.objects.count()
    return f"{uploaded['name']} uploaded ({total} contacts)"
