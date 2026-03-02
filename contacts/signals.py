from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Contact


@receiver(post_save, sender=Contact)
def send_sms_on_new_contact(sender, instance, created, **kwargs):
    if created and not instance.whatsapp_message_sent:
        try:
            import africastalking
            africastalking.initialize(
                username=settings.AFRICASTALKING_USERNAME,
                api_key=settings.AFRICASTALKING_API_KEY
            )
            sms = africastalking.SMS
            phone = instance.whatsapp_contact.strip().replace(' ', '')
            if not phone.startswith('+'):
                phone = '+' + phone
            message = (
                f"Hi {instance.first_name}! "
                f"Welcome to SK Network. Your details have been received successfully. "
                f"We have added you as a {instance.get_category_display()} "
                f"on {instance.get_social_media_platform_display()}. "
                f"Our team will be in touch shortly. - SK Team"
            )
            sms.send(message=message, recipients=[phone])
            instance.whatsapp_message_sent = True
            instance.save(update_fields=['whatsapp_message_sent'])
            print(f"✅ SMS sent to {instance.first_name} ({phone})")
        except Exception as e:
            print(f"❌ SMS failed: {str(e)}")