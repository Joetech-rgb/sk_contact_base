from django import forms
from .models import Contact, Category

# ─────────────────────────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────────────────────────

DIAL_CODE_CHOICES = [
    ("",     "Code"),
    ("+233", "🇬🇭 +233"),   # Ghana — default
    ("+234", "🇳🇬 +234"),
    ("+1",   "🇺🇸 +1"),
    ("+44",  "🇬🇧 +44"),
    ("+27",  "🇿🇦 +27"),
    ("+254", "🇰🇪 +254"),
    ("+20",  "🇪🇬 +20"),
    ("+212", "🇲🇦 +212"),
    ("+213", "🇩🇿 +213"),
    ("+216", "🇹🇳 +216"),
    ("+221", "🇸🇳 +221"),
    ("+225", "🇨🇮 +225"),
    ("+230", "🇲🇺 +230"),
    ("+231", "🇱🇷 +231"),
    ("+232", "🇸🇱 +232"),
    ("+235", "🇹🇩 +235"),
    ("+237", "🇨🇲 +237"),
    ("+241", "🇬🇦 +241"),
    ("+242", "🇨🇬 +242"),
    ("+243", "🇨🇩 +243"),
    ("+244", "🇦🇴 +244"),
    ("+249", "🇸🇩 +249"),
    ("+250", "🇷🇼 +250"),
    ("+251", "🇪🇹 +251"),
    ("+255", "🇹🇿 +255"),
    ("+256", "🇺🇬 +256"),
    ("+260", "🇿🇲 +260"),
    ("+263", "🇿🇼 +263"),
    ("+265", "🇲🇼 +265"),
    ("+267", "🇧🇼 +267"),
    ("+268", "🇸🇿 +268"),
    ("+269", "🇰🇲 +269"),
    ("+91",  "🇮🇳 +91"),
    ("+86",  "🇨🇳 +86"),
    ("+81",  "🇯🇵 +81"),
    ("+82",  "🇰🇷 +82"),
    ("+61",  "🇦🇺 +61"),
    ("+33",  "🇫🇷 +33"),
    ("+49",  "🇩🇪 +49"),
    ("+39",  "🇮🇹 +39"),
    ("+34",  "🇪🇸 +34"),
    ("+7",   "🇷🇺 +7"),
    ("+55",  "🇧🇷 +55"),
    ("+52",  "🇲🇽 +52"),
    ("+971", "🇦🇪 +971"),
    ("+966", "🇸🇦 +966"),
    ("+355", "🇦🇱 +355"),
    ("+43",  "🇦🇹 +43"),
    ("+994", "🇦🇿 +994"),
    ("+32",  "🇧🇪 +32"),
    ("+387", "🇧🇦 +387"),
    ("+359", "🇧🇬 +359"),
    ("+385", "🇭🇷 +385"),
    ("+357", "🇨🇾 +357"),
    ("+420", "🇨🇿 +420"),
    ("+45",  "🇩🇰 +45"),
    ("+372", "🇪🇪 +372"),
    ("+358", "🇫🇮 +358"),
    ("+30",  "🇬🇷 +30"),
    ("+36",  "🇭🇺 +36"),
    ("+354", "🇮🇸 +354"),
    ("+353", "🇮🇪 +353"),
    ("+972", "🇮🇱 +972"),
    ("+371", "🇱🇻 +371"),
    ("+370", "🇱🇹 +370"),
    ("+352", "🇱🇺 +352"),
    ("+356", "🇲🇹 +356"),
    ("+31",  "🇳🇱 +31"),
    ("+47",  "🇳🇴 +47"),
    ("+48",  "🇵🇱 +48"),
    ("+351", "🇵🇹 +351"),
    ("+40",  "🇷🇴 +40"),
    ("+381", "🇷🇸 +381"),
    ("+421", "🇸🇰 +421"),
    ("+386", "🇸🇮 +386"),
    ("+46",  "🇸🇪 +46"),
    ("+41",  "🇨🇭 +41"),
    ("+90",  "🇹🇷 +90"),
    ("+380", "🇺🇦 +380"),
]

AGE_RANGE_CHOICES = [
    ("",         "Select age range"),
    ("under_18", "Under 18"),
    ("18_24",    "18 – 24"),
    ("25_34",    "25 – 34"),
    ("35_44",    "35 – 44"),
    ("45_54",    "45 – 54"),
    ("55_plus",  "55+"),
]

PLATFORM_CHOICES = [
    ("",          "Select platform"),
    ("instagram", "Instagram"),
    ("tiktok",    "TikTok"),
    ("facebook",  "Facebook"),
    ("twitter",   "Twitter / X"),
    ("youtube",   "YouTube"),
    ("snapchat",  "Snapchat"),
    ("linkedin",  "LinkedIn"),
    ("other",     "Other"),
]

FOLLOWER_RANGE_CHOICES = [
    ("",          "Select range"),
    ("under_5k",  "Under 5K"),
    ("5k-10k",    "5K – 10K"),
    ("10k-50k",   "10K – 50K"),
    ("50k-100k",  "50K – 100K"),
    ("100k-250k", "100K – 250K"),
    ("250k-500k", "250K – 500K"),
    ("500k-1M",   "500K – 1M"),
    ("1M+",       "1M+"),
]

SCHOOL_CATEGORY_CHOICES = [
    ("",           "Select school type"),
    ("basic",      "Basic School"),
    ("high_school","High School"),
    ("tertiary",   "Tertiary"),
]


# ─────────────────────────────────────────────────────────────
# FORM
# ─────────────────────────────────────────────────────────────

class ContactForm(forms.ModelForm):

    # Non-model field: the dial code selector rendered beside the number input
    whatsapp_dial_code = forms.ChoiceField(
        choices=DIAL_CODE_CHOICES,
        initial="+233",
        required=True,
        widget=forms.Select(attrs={
            "id":    "id_dial_code",
            "class": "form-control",
        }),
    )

    class Meta:
        model  = Contact
        fields = [
            "first_name", "surname", "email",
            "whatsapp_number", "country_code",
            "age_range", "country", "region",
            "category", "school_category", "school_name", "level_year",
            "platform", "handle", "follower_range",
            "referral_source", "referral_slug",
        ]

        widgets = {
            # Basic
            "first_name": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "First name",
            }),
            "surname": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Surname",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control", "placeholder": "your@email.com",
            }),
            "whatsapp_number": forms.TextInput(attrs={
                "class": "form-control", "id": "id_whatsapp_number",
                "placeholder": "Number without code",
            }),
            "country_code": forms.HiddenInput(attrs={"id": "id_country_code"}),

            # Profile
            "age_range": forms.Select(
                attrs={"class": "form-control"},
                choices=AGE_RANGE_CHOICES,
            ),
            "country": forms.TextInput(attrs={
                "class": "form-control", "id": "id_country",
                "placeholder": "Auto-filled from dial code",
            }),
            "region": forms.TextInput(attrs={
                "class": "form-control", "id": "id_region",
                "placeholder": "e.g. Greater Accra, Ashanti…",
            }),

            # Optional
            "school_category": forms.Select(
                attrs={"class": "form-control"},
                choices=SCHOOL_CATEGORY_CHOICES,
            ),
            "school_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Name of school or university",
            }),
            "level_year": forms.NumberInput(attrs={
                "class": "form-control", "placeholder": "e.g. 2",
                "min": "1", "max": "10",
            }),

            # Social
            "platform": forms.Select(
                attrs={"class": "form-control"},
                choices=PLATFORM_CHOICES,
            ),
            "handle": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "username or @username",
            }),
            "follower_range": forms.Select(
                attrs={"class": "form-control"},
                choices=FOLLOWER_RANGE_CHOICES,
            ),

            # Tracking (hidden — populated by view from ?ref= param)
            "referral_source": forms.HiddenInput(),
            "referral_slug":   forms.HiddenInput(attrs={"id": "id_referral_slug"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Category: pull only active ones for the form
        self.fields["category"].queryset    = Category.objects.filter(is_active=True)
        self.fields["category"].empty_label = "Select a category"
        self.fields["category"].required    = False

        # Optional fields
        for f in ["school_category", "school_name", "level_year",
                  "category", "region", "handle", "country_code",
                  "age_range", "platform", "follower_range",
                  "referral_source", "referral_slug"]:
            self.fields[f].required = False

        # Required fields
        for f in ["first_name", "surname", "email",
                  "whatsapp_number", "whatsapp_dial_code"]:
            self.fields[f].required = True

    # ── Validation ──────────────────────────────────────────

    def clean_level_year(self):
        val = self.cleaned_data.get("level_year")
        if val is not None and val < 1:
            raise forms.ValidationError("Level must be a positive number.")
        return val

    def clean_handle(self):
        """Strip @ prefix — always store without it."""
        return self.cleaned_data.get("handle", "").lstrip("@")

    def clean_whatsapp_number(self):
        """
        JS prepends the dial code before submit, so by the time this runs
        the value should already be e.g. +233241234567.
        We strip whitespace and enforce uniqueness with a clear message.
        """
        num = self.cleaned_data.get("whatsapp_number", "").strip().replace(" ", "")
        if not num:
            raise forms.ValidationError("WhatsApp number is required.")
        # Uniqueness check — friendly message
        qs = Contact.objects.filter(whatsapp_number=num)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "This WhatsApp number is already registered. "
                "One contact cannot register more than once."
            )
        return num

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = Contact.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "This email address is already registered. "
                "One contact cannot register more than once."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        # Mirror dial code into the hidden country_code field if JS didn't
        dial = cleaned.get("whatsapp_dial_code", "")
        if dial and not cleaned.get("country_code"):
            cleaned["country_code"] = dial
        return cleaned