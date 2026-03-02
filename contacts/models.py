from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Contact(models.Model):
    """
    Enhanced Contact Model for SK Contact Base
    Manages influencer/content creator contacts with comprehensive tracking
    """

    # Category Choices
    CATEGORY_CHOICES = [
        ('face_card',   'Face Card'),
        ('chubby',      'Chubby'),
        ('brand_owner', 'Brand Owner'),
        ('slim',        'Slim'),
        ('curvy',       'Curvy'),
        ('dark_skin',   'Dark Skin'),
        ('half_cast',   'Half Cast'),
    ]

    # Age Category Choices — expanded to 60+
    AGE_CATEGORY_CHOICES = [
        ('18-24', '18 – 24'),
        ('25-30', '25 – 30'),
        ('31-35', '31 – 35'),
        ('36-40', '36 – 40'),
        ('41-45', '41 – 45'),
        ('46-50', '46 – 50'),
        ('51-55', '51 – 55'),
        ('56-60', '56 – 60'),
        ('60+',   '60+'),
    ]

    # Social Media Platform Choices
    SOCIAL_MEDIA_CHOICES = [
        ('linkedin',  'LinkedIn'),
        ('instagram', 'Instagram'),
        ('facebook',  'Facebook'),
        ('snapchat',  'Snapchat'),
        ('tiktok',    'TikTok'),
        ('twitter',   'Twitter/X'),
        ('youtube',   'YouTube'),
    ]

    # Phone number validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    # ── Basic Information ──
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    surname    = models.CharField(max_length=100, verbose_name="Surname")
    email      = models.EmailField(blank=True, null=True, verbose_name="Email")
    whatsapp_contact = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="WhatsApp Contact",
        help_text="Include country code, e.g., +233XXXXXXXXX"
    )

    # ── Categorisation ──
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Category"
    )
    age_category = models.CharField(
        max_length=10,
        choices=AGE_CATEGORY_CHOICES,
        verbose_name="Age Category"
    )
    country = models.CharField(max_length=100, verbose_name="Country")
    country_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Country Code",
        help_text="e.g., +233, +1, +44"
    )

    # ── Social Media Information ──
    social_media_platform = models.CharField(
        max_length=20,
        choices=SOCIAL_MEDIA_CHOICES,
        verbose_name="Social Media Platform"
    )
    social_media_handle = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Social Media Handle"
    )
    followers_count = models.IntegerField(
        default=0,
        verbose_name="Followers Count",
        help_text="Current follower count"
    )

    # ── Additional Information ──
    school = models.CharField(max_length=200, blank=True, null=True, verbose_name="School")
    level  = models.CharField(max_length=100, blank=True, null=True, verbose_name="Level/Grade")
    notes  = models.TextField(blank=True, null=True, verbose_name="Notes")

    # ── Tracking ──
    date_added   = models.DateTimeField(auto_now_add=True, verbose_name="Date Added")
    last_updated = models.DateTimeField(auto_now=True,     verbose_name="Last Updated")
    whatsapp_message_sent = models.BooleanField(default=False, verbose_name="WhatsApp Message Sent")
    whatsapp_message_date = models.DateTimeField(blank=True, null=True, verbose_name="WhatsApp Message Date")
    synced_to_drive = models.BooleanField(default=False, verbose_name="Synced to Google Drive")

    class Meta:
        ordering = ['-followers_count', '-date_added']
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['country']),
            models.Index(fields=['social_media_platform']),
            models.Index(fields=['-followers_count']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.surname} | {self.get_category_display()} | {self.country} | {self.get_social_media_platform_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.surname}"

    @property
    def days_since_added(self):
        return (timezone.now() - self.date_added).days

    def get_whatsapp_link(self):
        clean_number = ''.join(filter(str.isdigit, self.whatsapp_contact))
        return f"https://wa.me/{clean_number}"

    def save(self, *args, **kwargs):
        """Auto-extract country code from WhatsApp number if not set."""
        if self.whatsapp_contact and not self.country_code:
            if self.whatsapp_contact.startswith('+'):
                parts = self.whatsapp_contact[1:].split()
                if parts:
                    self.country_code = '+' + ''.join(filter(str.isdigit, parts[0][:4]))
        super().save(*args, **kwargs)


class ContactStats(models.Model):
    """Track overall statistics for the contact base."""
    date = models.DateField(unique=True, verbose_name="Date")
    total_contacts       = models.IntegerField(default=0, verbose_name="Total Contacts")
    contacts_added_today = models.IntegerField(default=0, verbose_name="Contacts Added Today")

    class Meta:
        ordering = ['-date']
        verbose_name = "Contact Statistics"
        verbose_name_plural = "Contact Statistics"

    def __str__(self):
        return f"Stats for {self.date}: {self.total_contacts} total contacts"


class AutomationLog(models.Model):
    """Log automation activities (WhatsApp messages, Drive syncs, exports)."""
    ACTION_CHOICES = [
        ('whatsapp',   'WhatsApp Message'),
        ('drive_sync', 'Google Drive Sync'),
        ('export',     'Data Export'),
    ]

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='automation_logs',
        verbose_name="Contact"
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action Type")
    timestamp   = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    status      = models.CharField(max_length=20, verbose_name="Status")
    details     = models.TextField(blank=True, verbose_name="Details")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Automation Log"
        verbose_name_plural = "Automation Logs"

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.contact.full_name} - {self.timestamp}"