"""
Background tasks for SK Contact Base

NOTE:
This file intentionally contains simple task wrappers.
It can later be upgraded to Celery or Django-Q if needed.
"""

from django.utils import timezone
from datetime import timedelta

from .models import Contact
from .Automations import WhatsAppAutomation, DailyStatsUpdater, GoogleDriveAutomation


def send_whatsapp_to_new_contacts(hours=24):
    """
    Send WhatsApp messages to contacts added within the last X hours
    """
    cutoff_time = timezone.now() - timedelta(hours=hours)

    contacts = Contact.objects.filter(
        whatsapp_message_sent=False,
        date_added__gte=cutoff_time
    )

    if not contacts.exists():
        return 0

    whatsapp = WhatsAppAutomation()
    sent_count = 0

    for contact in contacts:
        if whatsapp.send_welcome_message(contact):
            sent_count += 1

    return sent_count


def update_daily_contact_stats():
    """
    Update or create daily contact statistics
    """
    return DailyStatsUpdater.update_stats()


def run_google_drive_backup():
    """
    Run Google Drive backup for all contacts
    """
    drive = GoogleDriveAutomation()
    return drive.upload_contacts_backup()
