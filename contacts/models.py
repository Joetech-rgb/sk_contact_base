from django.db import models
from django.utils import timezone


class GoogleToken(models.Model):
    email         = models.EmailField()
    access_token  = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_expiry  = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'contacts'

    def __str__(self):
        return f"Google token â€” {self.email}"

    def set_expiry(self, expiry):
        """
        Safely store token expiry â€” ensures datetime is always timezone-aware.
        Call this instead of setting token_expiry directly.
        """
        if expiry is None:
            self.token_expiry = None
        elif expiry.tzinfo is None:
            self.token_expiry = timezone.make_aware(expiry)
        else:
            self.token_expiry = expiry


class Category(models.Model):
    """
    Admin-managed categories shown in the registration form.
    Admin can add, edit, remove and toggle visibility of categories.
    """
    name       = models.CharField(max_length=100, unique=True)
    is_active  = models.BooleanField(
                     default=True,
                     help_text="Uncheck to hide this category from the registration form "
                               "without deleting it. It stays in downloaded contact data.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReferralSource(models.Model):
    """
    Tracks which link/platform brought the registrant.
    Used for conversion rate reporting in the admin dashboard.
    """
    slug        = models.SlugField(
                      max_length=100, unique=True,
                      help_text="Short identifier used in the URL parameter e.g. 'ig-bio'")
    label       = models.CharField(
                      max_length=200,
                      help_text="Human-readable label e.g. 'Instagram Bio Link'")
    is_active   = models.BooleanField(default=True)
    click_count = models.PositiveIntegerField(
                      default=0,
                      help_text="Incremented each time someone visits the landing page via this link.")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Referral Source"
        verbose_name_plural = "Referral Sources"
        ordering            = ["label"]

    def __str__(self):
        return self.label


class Contact(models.Model):

    SCHOOL_CATEGORY_CHOICES = [
        ("basic",       "Basic School"),
        ("high_school", "High School"),
        ("tertiary",    "Tertiary"),
    ]

    FOLLOWER_RANGE_CHOICES = [
        ("under_5k",  "Under 5K"),
        ("5k-10k",    "5K â€“ 10K"),
        ("10k-50k",   "10K â€“ 50K"),
        ("50k-100k",  "50K â€“ 100K"),
        ("100k-250k", "100K â€“ 250K"),
        ("250k-500k", "250K â€“ 500K"),
        ("500k-1M",   "500K â€“ 1M"),
        ("1M+",       "1M+"),
    ]

    # â”€â”€ Basic details â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    first_name      = models.CharField(max_length=100)
    surname         = models.CharField(max_length=100)
    email           = models.EmailField(
                          unique=True,
                          help_text="Used to prevent duplicate registrations.")
    whatsapp_number = models.CharField(
                          max_length=25, unique=True,
                          help_text="Stored as full international number e.g. +233241234567")
    country_code    = models.CharField(
                          max_length=10, blank=True,
                          help_text="Dial code e.g. +233. Auto-set from WhatsApp selector.")

    # â”€â”€ Profile â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    age_range       = models.CharField(max_length=20, blank=True)
    country         = models.CharField(
                          max_length=100, blank=True,
                          help_text="Auto-filled from the WhatsApp country code selector.")
    region          = models.CharField(
                          max_length=150, blank=True,
                          help_text="Broad regional area, not a specific town.")

    # â”€â”€ Optional â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    category        = models.ForeignKey(
                          Category, on_delete=models.SET_NULL,
                          null=True, blank=True,
                          help_text="Selected in the optional pop-up during registration.")
    school_category = models.CharField(
                          max_length=20, choices=SCHOOL_CATEGORY_CHOICES, blank=True)
    school_name     = models.CharField(max_length=255, blank=True)
    level_year      = models.PositiveIntegerField(
                          null=True, blank=True,
                          help_text="Year or level as a number only.")

    # â”€â”€ Social media â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    platform        = models.CharField(max_length=50, blank=True)
    handle          = models.CharField(
                          max_length=100, blank=True,
                          help_text="Stored without @ prefix.")
    follower_range  = models.CharField(
                          max_length=50, choices=FOLLOWER_RANGE_CHOICES, blank=True)

    # â”€â”€ Referral / conversion tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    referral_source = models.ForeignKey(
                          ReferralSource, on_delete=models.SET_NULL,
                          null=True, blank=True,
                          help_text="Which link/platform brought this person here.")
    referral_slug   = models.CharField(
                          max_length=100, blank=True,
                          help_text="Raw slug captured from ?ref= URL parameter at registration.")

    # â”€â”€ Meta â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    date_added      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_added"]

    # â”€â”€ Properties â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    @property
    def full_name(self):
        return f"{self.first_name} {self.surname}"

    @property
    def full_whatsapp(self):
        """Always returns the number with country code prefix."""
        num = self.whatsapp_number or ""
        if num.startswith("+"):
            return num
        return f"{self.country_code}{num}"

    @property
    def whatsapp_chat_url(self):
        clean = self.full_whatsapp.replace("+", "").replace(" ", "")
        return f"https://wa.me/{clean}"

    @property
    def handle_clean(self):
        """Handle without @ symbol."""
        return (self.handle or "").lstrip("@")

    @property
    def platform_profile_url(self):
        h = self.handle_clean
        if not h:
            return None
        urls = {
            "instagram": f"https://instagram.com/{h}",
            "tiktok":    f"https://tiktok.com/@{h}",
            "facebook":  f"https://facebook.com/{h}",
            "twitter":   f"https://twitter.com/{h}",
            "youtube":   f"https://youtube.com/@{h}",
            "snapchat":  f"https://snapchat.com/add/{h}",
            "linkedin":  f"https://linkedin.com/in/{h}",
        }
        return urls.get(self.platform)

    @property
    def days_since_added(self):
        return (timezone.now().date() - self.date_added.date()).days

    def __str__(self):
        return f"{self.full_name} ({self.country})"

class WhatsAppLog(models.Model):
    """Records every WhatsApp send attempt for delivery tracking."""

    STATUS_CHOICES = [
        ("sent",    "Sent"),
        ("failed",  "Failed"),
        ("fallback","SMS Fallback"),
    ]

    contact   = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    template  = models.CharField(max_length=100)
    phone     = models.CharField(max_length=25)
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    error     = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name     = "WhatsApp Log"
        verbose_name_plural = "WhatsApp Logs"

    def __str__(self):
        return f"{self.phone} — {self.template} — {self.status} ({self.timestamp:%Y-%m-%d %H:%M})"



class Notification(models.Model):
    TYPE_CHOICES = [
        ("job",       "Job"),
        ("giveaway",  "Giveaway"),
        ("link",      "Link"),
        ("other",     "Other"),
    ]
    title        = models.CharField(max_length=200)
    body         = models.TextField()
    type         = models.CharField(max_length=20, choices=TYPE_CHOICES, default="other")
    is_active    = models.BooleanField(default=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.type.upper()}] {self.title}"



class BulkMessage(models.Model):
    """Records every bulk WhatsApp send for audit trail."""
    STATUS_CHOICES = [
        ("pending",  "Pending"),
        ("sending",  "Sending"),
        ("done",     "Done"),
        ("failed",   "Failed"),
    ]
    template      = models.CharField(max_length=100)
    filter_params = models.JSONField(default=dict)
    sent_count    = models.PositiveIntegerField(default=0)
    failed_count  = models.PositiveIntegerField(default=0)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_by    = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bulk Message"
        verbose_name_plural = "Bulk Messages"

    def __str__(self):
        return f"Bulk {self.template} — {self.status} ({self.created_at:%Y-%m-%d})"


class ServiceRequest(models.Model):
    """Brand or individual requesting a filtered contact export."""
    STATUS_CHOICES = [
        ("pending",  "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("fulfilled","Fulfilled"),
    ]
    requester_name   = models.CharField(max_length=200)
    email            = models.EmailField()
    phone            = models.CharField(max_length=25)
    filter_criteria  = models.JSONField(default=dict, help_text="e.g. country, category, follower range")
    budget           = models.CharField(max_length=100, blank=True)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_at     = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return f"{self.requester_name} — {self.status} ({self.submitted_at:%Y-%m-%d})"

