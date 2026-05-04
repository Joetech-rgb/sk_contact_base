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

    # ── Basic details ──────────────────────────────────────
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

    # ── Profile ────────────────────────────────────────────
    age_range       = models.CharField(max_length=20, blank=True)
    country         = models.CharField(
                          max_length=100, blank=True,
                          help_text="Auto-filled from the WhatsApp country code selector.")
    region          = models.CharField(
                          max_length=150, blank=True,
                          help_text="Broad regional area, not a specific town.")

    # ── Optional ───────────────────────────────────────────
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

    # ── Social media ───────────────────────────────────────
    platform        = models.CharField(max_length=50, blank=True)
    handle          = models.CharField(
                          max_length=100, blank=True,
                          help_text="Stored without @ prefix.")
    follower_range  = models.CharField(
                          max_length=50, choices=FOLLOWER_RANGE_CHOICES, blank=True)

    # ── Referral / conversion tracking ────────────────────
    referral_source = models.ForeignKey(
                          ReferralSource, on_delete=models.SET_NULL,
                          null=True, blank=True,
                          help_text="Which link/platform brought this person here.")
    referral_slug   = models.CharField(
                          max_length=100, blank=True,
                          help_text="Raw slug captured from ?ref= URL parameter at registration.")

    # ── Meta ───────────────────────────────────────────────
    date_added      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_added"]

    # ── Properties ─────────────────────────────────────────
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