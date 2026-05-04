"""
Background tasks for SK Contact Base.
Use this to orchestrate automated workflows.
"""

from django.utils import timezone
from datetime import timedelta
from .models import Contact
from .Automations import WhatsAppAutomation, DailyStatsUpdater, GoogleDriveAutomation

def send_whatsapp_to_new_contacts(hours=24):
    """
    Sends WhatsApp messages to contacts added within the last X hours
    that haven't been messaged yet.
    """
    cutoff_time = timezone.now() - timedelta(hours=hours)
    
    # Correctly query the Contact model, not the module
    contacts_to_message = Contact.objects.filter(
        whatsapp_message_sent=False,
        date_added__gte=cutoff_time
    )

    if not contacts_to_message.exists():
        return 0

    whatsapp = WhatsAppAutomation()
    sent_count = 0

    for contact in contacts_to_message:
        try:
            # Attempt to send and verify success
            if whatsapp.send_welcome_message(contact):
                contact.whatsapp_message_sent = True
                contact.save()
                sent_count += 1
        except Exception as e:
            # Log the error; using print() is fine for small scale, 
            # but consider using standard logging in the future.
            print(f"Error processing contact {contact.id}: {str(e)}")
            
    return sent_count

def update_daily_contact_stats():
    """
    Update or create daily contact statistics via the stats updater.
    """
    try:
        return DailyStatsUpdater.update_stats()
    except Exception as e:
        print(f"Stats update failed: {str(e)}")
        return False

def run_google_drive_backup():
    """
    Run Google Drive backup for all contacts.
    """
    try:
        drive = GoogleDriveAutomation()
        return drive.upload_contacts_backup()
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        return False