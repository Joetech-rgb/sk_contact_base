from django.db import models
from django.utils import timezone
import hashlib as _hashlib
import secrets as _secrets


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
        return f"Google token — {self.email}"

    def set_expiry(self, expiry):
        """
        Safely store token expiry — ensures datetime is always timezone-aware.
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

    @property
    def contact_count(self):
        return self.contact_set.count()


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
        ("5k-10k",    "5K – 10K"),
        ("10k-50k",   "10K – 50K"),
        ("50k-100k",  "50K – 100K"),
        ("100k-250k", "100K – 250K"),
        ("250k-500k", "250K – 500K"),
        ("500k-1M",   "500K – 1M"),
        ("1M+",       "1M+"),
    ]

    # ── Basic details ──────────────────────────────────────────────
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

    # ── Profile ────────────────────────────────────────────────────
    age_range       = models.CharField(max_length=20, blank=True)
    country         = models.CharField(
                          max_length=100, blank=True,
                          help_text="Auto-filled from the WhatsApp country code selector.")
    region          = models.CharField(
                          max_length=150, blank=True,
                          help_text="Broad regional area, not a specific town.")

    # ── Optional ───────────────────────────────────────────────────
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

    # ── Social media ───────────────────────────────────────────────
    platform        = models.CharField(max_length=50, blank=True)
    handle          = models.CharField(
                          max_length=100, blank=True,
                          help_text="Stored without @ prefix.")
    follower_range  = models.CharField(
                          max_length=50, choices=FOLLOWER_RANGE_CHOICES, blank=True)

    # ── Referral / conversion tracking ────────────────────────────
    referral_source = models.ForeignKey(
                          ReferralSource, on_delete=models.SET_NULL,
                          null=True, blank=True,
                          help_text="Which link/platform brought this person here.")
    referral_slug   = models.CharField(
                          max_length=100, blank=True,
                          help_text="Raw slug captured from ?ref= URL parameter at registration.")

    # ── Meta ───────────────────────────────────────────────────────
    date_added      = models.DateTimeField(auto_now_add=True)
    agreed_to_terms = models.DateTimeField(null=True, blank=True)
    opted_out       = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_added"]
        indexes = [
            models.Index(fields=["date_added"]),
            models.Index(fields=["country"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["whatsapp_number"]),
            models.Index(fields=["email"]),
        ]

    # ── Properties ─────────────────────────────────────────────────
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
    STATUS_CHOICES = [
        ("sent",     "Sent"),
        ("failed",   "Failed"),
        ("fallback", "SMS Fallback"),
        ("received", "Received"),  # ADD THIS
    ]

    contact      = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    template     = models.CharField(max_length=100)
    phone        = models.CharField(max_length=25)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    error        = models.TextField(blank=True)
    message_text = models.TextField(blank=True)   # ADD THIS — stores incoming reply text
    direction    = models.CharField(              # ADD THIS — 'in' or 'out'
                       max_length=5,
                       default="out",
                       choices=[("in","Inbound"),("out","Outbound")]
                   )
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name        = "WhatsApp Log"
        verbose_name_plural = "WhatsApp Logs"

    def __str__(self):
        return f"{self.phone} — {self.template} — {self.status} ({self.timestamp:%Y-%m-%d %H:%M})"

class Notification(models.Model):
    TYPE_CHOICES = [
        ("job",      "Job"),
        ("giveaway", "Giveaway"),
        ("link",     "Link"),
        ("other",    "Other"),
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
        ("pending", "Pending"),
        ("sending", "Sending"),
        ("done",    "Done"),
        ("failed",  "Failed"),
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
        verbose_name        = "Bulk Message"
        verbose_name_plural = "Bulk Messages"

    def __str__(self):
        return f"Bulk {self.template} — {self.status} ({self.created_at:%Y-%m-%d})"


class ServiceRequest(models.Model):
    """Brand or individual requesting a filtered contact export."""
    STATUS_CHOICES = [
        ("pending",   "Pending"),
        ("approved",  "Approved"),
        ("rejected",  "Rejected"),
        ("fulfilled", "Fulfilled"),
    ]
    requester_name  = models.CharField(max_length=200)
    email           = models.EmailField()
    phone           = models.CharField(max_length=25)
    filter_criteria = models.JSONField(default=dict, help_text="e.g. country, category, follower range")
    budget          = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_at    = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name        = "Service Request"
        verbose_name_plural = "Service Requests"

    def __str__(self):
        return f"{self.requester_name} — {self.status} ({self.submitted_at:%Y-%m-%d})"


class APIKey(models.Model):
    name       = models.CharField(max_length=100)
    key_hash   = models.CharField(max_length=64, unique=True, editable=False)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used  = models.DateTimeField(null=True, blank=True)
    use_count  = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = 'API Key'
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return self.name

    @classmethod
    def create(cls, name):
        raw    = _secrets.token_urlsafe(32)
        hashed = _hashlib.sha256(raw.encode()).hexdigest()
        obj    = cls.objects.create(name=name, key_hash=hashed)
        return obj, raw

    def record_use(self):
        APIKey.objects.filter(pk=self.pk).update(
            last_used=timezone.now(),
            use_count=models.F('use_count') + 1,
        )


class Campaign(models.Model):
    STATUS_CHOICES = [
        ("draft",    "Draft"),
        ("active",   "Active"),
        ("complete", "Complete"),
    ]
    name              = models.CharField(max_length=200)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    target_categories = models.ManyToManyField(Category, blank=True)
    target_country    = models.CharField(max_length=100, blank=True)
    template_name     = models.CharField(max_length=100, blank=True)
    notes             = models.TextField(blank=True)
    campaign_message  = models.TextField(blank=True)
    contacted_count   = models.PositiveIntegerField(default=0)
    responded_count   = models.PositiveIntegerField(default=0)
    confirmed_count   = models.PositiveIntegerField(default=0)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def response_rate(self):
        if self.contacted_count == 0:
            return 0
        return round((self.responded_count / self.contacted_count) * 100)

    @property
    def conversion_rate(self):
        if self.contacted_count == 0:
            return 0
        return round((self.confirmed_count / self.contacted_count) * 100)


class CommunityPost(models.Model):
    TYPE_CHOICES = [
        ("announcement", "Announcement"),
        ("campaign",     "Campaign"),
        ("milestone",    "Milestone"),
        ("testimonial",  "Testimonial"),
        ("video",        "Video"),
    ]
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default="announcement")
    title      = models.CharField(max_length=200)
    content    = models.TextField()
    author     = models.CharField(
                     max_length=200, blank=True,
                     help_text="For testimonials: format as 'Name, Location' e.g. 'Abena K., Accra'")
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    # ── Display helpers used by the landing page template ──────────

    @property
    def author_name(self):
        """First part of author field: 'Abena K.' from 'Abena K., Accra'"""
        if not self.author:
            return "Anonymous"
        return self.author.split(",")[0].strip()

    @property
    def author_role(self):
        """Second part of author field: 'Accra' from 'Abena K., Accra'"""
        if not self.author or "," not in self.author:
            return ""
        return self.author.split(",", 1)[1].strip()

    @property
    def author_initials(self):
        """Two-letter initials from author_name e.g. 'AK' from 'Abena K.'"""
        parts = self.author_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return parts[0][:2].upper() if parts else "??"

    @property
    def likes(self):
        """Placeholder — add a LikeCount model later if needed."""
        return 0

    @property
    def views(self):
        """Placeholder for video view counts."""
        return 0

    @property
    def tag_class(self):
        """CSS class name — maps directly to the post type."""
        return self.type

    @property
    def tag_label(self):
        """Human-readable type label for the landing page badge."""
        return self.get_type_display()

    @property
    def thumbnail_url(self):
        """Placeholder — no image upload field yet."""
        return ""

    @property
    def image_url(self):
        """Placeholder — no image upload field yet."""
        return ""


class WhatsAppTemplate(models.Model):
    name       = models.CharField(max_length=100, unique=True, help_text="Exact template name from Meta e.g. sk_welcome")
    label      = models.CharField(max_length=200, blank=True, help_text="Friendly label e.g. Welcome Message")
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AccountLink(models.Model):
    PLATFORM_CHOICES = [
        ("wadm",      "WhatsApp DM"),
        ("wach",      "WhatsApp Channel"),
        ("tiktok",    "TikTok"),
        ("instagram", "Instagram"),
        ("youtube",   "YouTube"),
        ("x",         "X (Twitter)"),
        ("facebook",  "Facebook"),
        ("snapchat",  "Snapchat"),
    ]
    platform   = models.CharField(max_length=20, choices=PLATFORM_CHOICES, unique=True)
    handle     = models.CharField(max_length=200, blank=True)
    url        = models.URLField(blank=True)
    followers  = models.CharField(max_length=50, blank=True)
    shares     = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.platform


class CampaignContact(models.Model):
    STATUS_CHOICES = [
        ("pending",       "Pending"),
        ("interested",    "Interested"),
        ("not_interested","Not Interested"),
        ("confirmed",     "Confirmed"),
    ]
    campaign   = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_contacts")
    contact    = models.ForeignKey(Contact,  on_delete=models.CASCADE, related_name="campaign_contacts")
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes      = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("campaign", "contact")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.contact.full_name} - {self.campaign.name} - {self.status}"


class CategoryChangeRequest(models.Model):
    """
    Submitted by a registered user who wants the admin to update their category.
    Looked up by WhatsApp number since that is unique per contact.
    """
    STATUS_CHOICES = [
        ("pending",  "Pending"),
        ("done",     "Done"),
        ("rejected", "Rejected"),
    ]

    whatsapp_number    = models.CharField(max_length=25)
    full_name          = models.CharField(max_length=200, blank=True)
    current_category   = models.CharField(
                             max_length=100, blank=True,
                             help_text="Auto-populated from the contact record at time of request.")
    requested_category = models.ForeignKey(
                             Category, on_delete=models.SET_NULL,
                             null=True, related_name="change_requests")
    reason             = models.TextField(blank=True)
    status             = models.CharField(
                             max_length=20, choices=STATUS_CHOICES, default="pending")
    submitted_at       = models.DateTimeField(auto_now_add=True)
    resolved_at        = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering            = ["-submitted_at"]
        verbose_name        = "Category Change Request"
        verbose_name_plural = "Category Change Requests"

    def __str__(self):
        return (
            f"{self.whatsapp_number} → {self.requested_category} "
            f"({self.status})"
        )


class SiteSettings(models.Model):
    """
    Singleton row for site-wide toggles controlled from the admin dashboard.
    Always use SiteSettings.load() to get the single instance — never
    create additional rows directly.
    """
    education_section_enabled = models.BooleanField(
        default=True,
        help_text="When off, the Education section is hidden from the "
                   "registration form's optional details pop-up for everyone.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # prevent deletion of the singleton row

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj