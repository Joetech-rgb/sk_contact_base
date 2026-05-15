# contacts/constants.py
# Single source of truth for all choice tuples and the dial-to-country map.

DIAL_TO_COUNTRY = {
    "+233": "Ghana", "+234": "Nigeria", "+1": "United States",
    "+44": "United Kingdom", "+27": "South Africa", "+254": "Kenya",
    "+20": "Egypt", "+212": "Morocco", "+213": "Algeria", "+216": "Tunisia",
    "+221": "Senegal", "+225": "Cote d Ivoire", "+230": "Mauritius",
    "+231": "Liberia", "+232": "Sierra Leone", "+235": "Chad",
    "+237": "Cameroon", "+241": "Gabon", "+242": "Republic of the Congo",
    "+243": "DR Congo", "+244": "Angola", "+249": "Sudan", "+250": "Rwanda",
    "+251": "Ethiopia", "+255": "Tanzania", "+256": "Uganda", "+260": "Zambia",
    "+263": "Zimbabwe", "+265": "Malawi", "+267": "Botswana", "+268": "Eswatini",
    "+269": "Comoros", "+91": "India", "+86": "China", "+81": "Japan",
    "+82": "South Korea", "+61": "Australia", "+33": "France", "+49": "Germany",
    "+39": "Italy", "+34": "Spain", "+7": "Russia", "+55": "Brazil",
    "+52": "Mexico", "+971": "United Arab Emirates", "+966": "Saudi Arabia",
    "+90": "Turkey", "+380": "Ukraine", "+48": "Poland", "+46": "Sweden",
    "+41": "Switzerland", "+31": "Netherlands", "+32": "Belgium", "+45": "Denmark",
    "+47": "Norway", "+353": "Ireland", "+351": "Portugal", "+40": "Romania",
    "+36": "Hungary", "+420": "Czech Republic", "+421": "Slovakia",
    "+43": "Austria", "+30": "Greece", "+358": "Finland", "+372": "Estonia",
    "+371": "Latvia", "+370": "Lithuania", "+357": "Cyprus", "+356": "Malta",
    "+354": "Iceland", "+386": "Slovenia", "+385": "Croatia", "+381": "Serbia",
    "+387": "Bosnia and Herzegovina", "+359": "Bulgaria", "+355": "Albania",
    "+994": "Azerbaijan", "+972": "Israel", "+352": "Luxembourg",
}

DIAL_CODE_CHOICES = [
    ("", "Code"),
    ("+233", "GH +233"), ("+234", "NG +234"), ("+1", "US +1"),
    ("+44", "GB +44"), ("+27", "ZA +27"), ("+254", "KE +254"),
    ("+20", "EG +20"), ("+212", "MA +212"), ("+213", "DZ +213"),
    ("+216", "TN +216"), ("+221", "SN +221"), ("+225", "CI +225"),
    ("+230", "MU +230"), ("+231", "LR +231"), ("+232", "SL +232"),
    ("+235", "TD +235"), ("+237", "CM +237"), ("+241", "GA +241"),
    ("+242", "CG +242"), ("+243", "CD +243"), ("+244", "AO +244"),
    ("+249", "SD +249"), ("+250", "RW +250"), ("+251", "ET +251"),
    ("+255", "TZ +255"), ("+256", "UG +256"), ("+260", "ZM +260"),
    ("+263", "ZW +263"), ("+265", "MW +265"), ("+267", "BW +267"),
    ("+268", "SZ +268"), ("+269", "KM +269"), ("+91", "IN +91"),
    ("+86", "CN +86"), ("+81", "JP +81"), ("+82", "KR +82"),
    ("+61", "AU +61"), ("+33", "FR +33"), ("+49", "DE +49"),
    ("+39", "IT +39"), ("+34", "ES +34"), ("+7", "RU +7"),
    ("+55", "BR +55"), ("+52", "MX +52"), ("+971", "AE +971"),
    ("+966", "SA +966"), ("+90", "TR +90"), ("+380", "UA +380"),
    ("+48", "PL +48"), ("+46", "SE +46"), ("+41", "CH +41"),
    ("+31", "NL +31"), ("+32", "BE +32"), ("+45", "DK +45"),
    ("+47", "NO +47"), ("+353", "IE +353"), ("+351", "PT +351"),
    ("+40", "RO +40"), ("+36", "HU +36"), ("+420", "CZ +420"),
    ("+43", "AT +43"), ("+30", "GR +30"), ("+358", "FI +358"),
    ("+372", "EE +372"), ("+371", "LV +371"), ("+370", "LT +370"),
    ("+357", "CY +357"), ("+354", "IS +354"), ("+386", "SI +386"),
    ("+385", "HR +385"), ("+381", "RS +381"), ("+355", "AL +355"),
    ("+972", "IL +972"), ("+352", "LU +352"),
]

AGE_RANGE_CHOICES = [
    ("", "Select age range"), ("under_18", "Under 18"), ("18_24", "18 - 24"),
    ("25_34", "25 - 34"), ("35_44", "35 - 44"), ("45_54", "45 - 54"), ("55_plus", "55+"),
]

PLATFORM_CHOICES = [
    ("", "Select platform"), ("instagram", "Instagram"), ("tiktok", "TikTok"),
    ("facebook", "Facebook"), ("twitter", "Twitter / X"), ("youtube", "YouTube"),
    ("snapchat", "Snapchat"), ("linkedin", "LinkedIn"), ("other", "Other"),
]

FOLLOWER_RANGE_CHOICES = [
    ("", "Select range"), ("under_5k", "Under 5K"), ("5k-10k", "5K - 10K"),
    ("10k-50k", "10K - 50K"), ("50k-100k", "50K - 100K"), ("100k-250k", "100K - 250K"),
    ("250k-500k", "250K - 500K"), ("500k-1M", "500K - 1M"), ("1M+", "1M+"),
]

SCHOOL_CATEGORY_CHOICES = [
    ("", "Select school type"), ("basic", "Basic School"),
    ("high_school", "High School"), ("tertiary", "Tertiary"),
]
