from django import forms
from .models import Contact

# Country list with (country_name, dial_code) tuples
COUNTRIES = [
    ("", "-- Select Country --"),
    ("Afghanistan", "+93"),
    ("Albania", "+355"),
    ("Algeria", "+213"),
    ("Andorra", "+376"),
    ("Angola", "+244"),
    ("Argentina", "+54"),
    ("Armenia", "+374"),
    ("Australia", "+61"),
    ("Austria", "+43"),
    ("Azerbaijan", "+994"),
    ("Bahamas", "+1-242"),
    ("Bahrain", "+973"),
    ("Bangladesh", "+880"),
    ("Belarus", "+375"),
    ("Belgium", "+32"),
    ("Belize", "+501"),
    ("Benin", "+229"),
    ("Bhutan", "+975"),
    ("Bolivia", "+591"),
    ("Bosnia and Herzegovina", "+387"),
    ("Botswana", "+267"),
    ("Brazil", "+55"),
    ("Brunei", "+673"),
    ("Bulgaria", "+359"),
    ("Burkina Faso", "+226"),
    ("Burundi", "+257"),
    ("Cambodia", "+855"),
    ("Cameroon", "+237"),
    ("Canada", "+1"),
    ("Cape Verde", "+238"),
    ("Central African Republic", "+236"),
    ("Chad", "+235"),
    ("Chile", "+56"),
    ("China", "+86"),
    ("Colombia", "+57"),
    ("Comoros", "+269"),
    ("Congo", "+242"),
    ("Costa Rica", "+506"),
    ("Croatia", "+385"),
    ("Cuba", "+53"),
    ("Cyprus", "+357"),
    ("Czech Republic", "+420"),
    ("Denmark", "+45"),
    ("Djibouti", "+253"),
    ("Dominican Republic", "+1-809"),
    ("DR Congo", "+243"),
    ("Ecuador", "+593"),
    ("Egypt", "+20"),
    ("El Salvador", "+503"),
    ("Equatorial Guinea", "+240"),
    ("Eritrea", "+291"),
    ("Estonia", "+372"),
    ("Eswatini", "+268"),
    ("Ethiopia", "+251"),
    ("Fiji", "+679"),
    ("Finland", "+358"),
    ("France", "+33"),
    ("Gabon", "+241"),
    ("Gambia", "+220"),
    ("Georgia", "+995"),
    ("Germany", "+49"),
    ("Ghana", "+233"),
    ("Greece", "+30"),
    ("Guatemala", "+502"),
    ("Guinea", "+224"),
    ("Guinea-Bissau", "+245"),
    ("Guyana", "+592"),
    ("Haiti", "+509"),
    ("Honduras", "+504"),
    ("Hungary", "+36"),
    ("Iceland", "+354"),
    ("India", "+91"),
    ("Indonesia", "+62"),
    ("Iran", "+98"),
    ("Iraq", "+964"),
    ("Ireland", "+353"),
    ("Israel", "+972"),
    ("Italy", "+39"),
    ("Ivory Coast", "+225"),
    ("Jamaica", "+1-876"),
    ("Japan", "+81"),
    ("Jordan", "+962"),
    ("Kazakhstan", "+7"),
    ("Kenya", "+254"),
    ("Kuwait", "+965"),
    ("Kyrgyzstan", "+996"),
    ("Laos", "+856"),
    ("Latvia", "+371"),
    ("Lebanon", "+961"),
    ("Lesotho", "+266"),
    ("Liberia", "+231"),
    ("Libya", "+218"),
    ("Lithuania", "+370"),
    ("Luxembourg", "+352"),
    ("Madagascar", "+261"),
    ("Malawi", "+265"),
    ("Malaysia", "+60"),
    ("Maldives", "+960"),
    ("Mali", "+223"),
    ("Malta", "+356"),
    ("Mauritania", "+222"),
    ("Mauritius", "+230"),
    ("Mexico", "+52"),
    ("Moldova", "+373"),
    ("Mongolia", "+976"),
    ("Montenegro", "+382"),
    ("Morocco", "+212"),
    ("Mozambique", "+258"),
    ("Myanmar", "+95"),
    ("Namibia", "+264"),
    ("Nepal", "+977"),
    ("Netherlands", "+31"),
    ("New Zealand", "+64"),
    ("Nicaragua", "+505"),
    ("Niger", "+227"),
    ("Nigeria", "+234"),
    ("North Korea", "+850"),
    ("North Macedonia", "+389"),
    ("Norway", "+47"),
    ("Oman", "+968"),
    ("Pakistan", "+92"),
    ("Panama", "+507"),
    ("Papua New Guinea", "+675"),
    ("Paraguay", "+595"),
    ("Peru", "+51"),
    ("Philippines", "+63"),
    ("Poland", "+48"),
    ("Portugal", "+351"),
    ("Qatar", "+974"),
    ("Romania", "+40"),
    ("Russia", "+7"),
    ("Rwanda", "+250"),
    ("Saudi Arabia", "+966"),
    ("Senegal", "+221"),
    ("Serbia", "+381"),
    ("Sierra Leone", "+232"),
    ("Singapore", "+65"),
    ("Slovakia", "+421"),
    ("Slovenia", "+386"),
    ("Somalia", "+252"),
    ("South Africa", "+27"),
    ("South Korea", "+82"),
    ("South Sudan", "+211"),
    ("Spain", "+34"),
    ("Sri Lanka", "+94"),
    ("Sudan", "+249"),
    ("Suriname", "+597"),
    ("Sweden", "+46"),
    ("Switzerland", "+41"),
    ("Syria", "+963"),
    ("Taiwan", "+886"),
    ("Tajikistan", "+992"),
    ("Tanzania", "+255"),
    ("Thailand", "+66"),
    ("Togo", "+228"),
    ("Trinidad and Tobago", "+1-868"),
    ("Tunisia", "+216"),
    ("Turkey", "+90"),
    ("Turkmenistan", "+993"),
    ("Uganda", "+256"),
    ("Ukraine", "+380"),
    ("United Arab Emirates", "+971"),
    ("United Kingdom", "+44"),
    ("United States", "+1"),
    ("Uruguay", "+598"),
    ("Uzbekistan", "+998"),
    ("Venezuela", "+58"),
    ("Vietnam", "+84"),
    ("Yemen", "+967"),
    ("Zambia", "+260"),
    ("Zimbabwe", "+263"),
]

# For the form dropdown choices (just country names)
COUNTRY_CHOICES = [(name, name) if name else ("", label) for name, label in COUNTRIES]

# For JS lookup: country name -> dial code (exported to template)
COUNTRY_DIAL_CODES = {name: code for name, code in COUNTRIES if name}


class ContactForm(forms.ModelForm):
    """
    Enhanced form for Contact creation and editing.
    Country is a simple dropdown. Selecting it auto-fills the country code.
    """

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_country',
        })
    )

    class Meta:
        model = Contact
        fields = [
            'first_name', 'surname', 'email', 'whatsapp_contact',
            'category', 'age_category', 'country', 'country_code',
            'social_media_platform', 'social_media_handle',
            'followers_count', 'school', 'level', 'notes',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
                'autocomplete': 'given-name',
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Surname',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'autocomplete': 'email',
            }),
            'whatsapp_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233XXXXXXXXX',
                'autocomplete': 'tel',
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'age_category': forms.Select(attrs={'class': 'form-control'}),
            'country_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+233',
                'autocomplete': 'off',
                'readonly': 'readonly',
            }),
            'social_media_platform': forms.Select(attrs={'class': 'form-control'}),
            'social_media_handle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username',
            }),
            'followers_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
            }),
            'school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'School / University (optional)',
            }),
            'level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Level / Grade (optional)',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)',
            }),
        }

    # ── Custom Validation ──────────────────────────────────────────────

    def clean_whatsapp_contact(self):
        """Validate and normalise WhatsApp number."""
        whatsapp = self.cleaned_data.get('whatsapp_contact', '')

        # Strip spaces and keep only digits and leading +
        whatsapp = ''.join(c for c in whatsapp if c.isdigit() or c == '+')

        # Fix duplicate country code (e.g. +2335+233540191971 -> +233540191971)
        if whatsapp.startswith('+'):
            whatsapp = '+' + whatsapp[1:].replace('+', '')

        if not whatsapp.startswith('+'):
            raise forms.ValidationError(
                "WhatsApp number must start with a country code (e.g. +233)"
            )

        if len(whatsapp) < 10:
            raise forms.ValidationError(
                "Please enter a valid WhatsApp number including country code."
            )

        return whatsapp

    def clean_followers_count(self):
        """Ensure followers count is not negative."""
        followers = self.cleaned_data.get('followers_count', 0)
        if followers is not None and followers < 0:
            raise forms.ValidationError("Followers count cannot be negative.")
        return followers

    def clean_country(self):
        """Ensure country field is not left empty."""
        country = self.cleaned_data.get('country', '').strip()
        if not country:
            raise forms.ValidationError("Please select your country.")
        return country