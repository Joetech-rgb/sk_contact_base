from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta, datetime as dt, date
import csv as csv_mod
import os

from .models import Contact, Category, ReferralSource
from .forms import ContactForm


DIAL_TO_COUNTRY = {
    "+233": "Ghana",          "+234": "Nigeria",        "+1":   "United States",
    "+44":  "United Kingdom", "+27":  "South Africa",   "+254": "Kenya",
    "+20":  "Egypt",          "+212": "Morocco",        "+213": "Algeria",
    "+216": "Tunisia",        "+221": "Senegal",        "+225": "Ivory Coast",
    "+230": "Mauritius",      "+231": "Liberia",        "+232": "Sierra Leone",
    "+235": "Chad",           "+237": "Cameroon",       "+241": "Gabon",
    "+242": "Congo",          "+243": "DR Congo",       "+244": "Angola",
    "+249": "Sudan",          "+250": "Rwanda",         "+251": "Ethiopia",
    "+255": "Tanzania",       "+256": "Uganda",         "+260": "Zambia",
    "+263": "Zimbabwe",       "+265": "Malawi",         "+267": "Botswana",
    "+268": "Eswatini",       "+269": "Comoros",        "+91":  "India",
    "+86":  "China",          "+81":  "Japan",          "+82":  "South Korea",
    "+61":  "Australia",      "+33":  "France",         "+49":  "Germany",
    "+39":  "Italy",          "+34":  "Spain",          "+7":   "Russia",
    "+55":  "Brazil",         "+52":  "Mexico",         "+971": "United Arab Emirates",
    "+966": "Saudi Arabia",   "+43":  "Austria",        "+32":  "Belgium",
    "+359": "Bulgaria",       "+385": "Croatia",        "+420": "Czech Republic",
    "+45":  "Denmark",        "+372": "Estonia",        "+358": "Finland",
    "+30":  "Greece",         "+36":  "Hungary",        "+353": "Ireland",
    "+972": "Israel",         "+371": "Latvia",         "+370": "Lithuania",
    "+31":  "Netherlands",    "+47":  "Norway",         "+48":  "Poland",
    "+351": "Portugal",       "+40":  "Romania",        "+381": "Serbia",
    "+46":  "Sweden",         "+41":  "Switzerland",    "+90":  "Turkey",
    "+380": "Ukraine",
}


# ── LOGIN / LOGOUT ──────────────────────────────────────────────────────────────

def admin_login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        error = "Invalid username or password."
    return render(request, "contacts/login.html", {"error": error})


def admin_logout_view(request):
    logout(request)
    return redirect("landing")


# ── LANDING PAGE ────────────────────────────────────────────────────────────────

def landing_view(request):
    ref_slug   = request.GET.get("ref", "").strip()
    ref_source = None

    if ref_slug:
        try:
            ref_source = ReferralSource.objects.get(slug=ref_slug, is_active=True)
            try:
                ReferralSource.objects.filter(pk=ref_source.pk).update(
                    click_count=ref_source.click_count + 1
                )
            except Exception:
                pass
        except ReferralSource.DoesNotExist:
            pass

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            dial = form.cleaned_data.get("whatsapp_dial_code", "")
            num  = contact.whatsapp_number or ""

            if num and not num.startswith("+"):
                contact.whatsapp_number = dial + num.lstrip("0")
            if not contact.country_code and dial:
                contact.country_code = dial
            if not contact.country and dial:
                contact.country = DIAL_TO_COUNTRY.get(dial, "")
            if contact.handle:
                contact.handle = contact.handle.lstrip("@")
            if ref_source:
                contact.referral_source = ref_source

            contact.referral_slug = (
                request.POST.get("referral_slug", "").strip() or ref_slug or ""
            )
            contact.save()

            request.session["contact_id"]   = contact.id
            request.session["contact_name"] = contact.full_name
            messages.success(
                request,
                f"Welcome {contact.first_name}! You're now part of the network.",
            )
            return redirect("thank-you")
    else:
        form = ContactForm()

    return render(request, "contacts/landing.html", {
        "form":              form,
        "total_contacts":    Contact.objects.count(),
        "active_categories": Category.objects.filter(is_active=True),
        "ref_slug":          ref_slug,
    })


# ── SMS / WHATSAPP HELPERS ──────────────────────────────────────────────────────

def _send_whatsapp_message(phone_number, message):
    try:
        from django.conf import settings
        import africastalking
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )
        sms        = africastalking.SMS
        response   = sms.send(message, [phone_number], sender_id="SKBRAND")
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        return any(r.get("status") == "Success" for r in recipients)
    except Exception as e:
        print(f"[WhatsApp] Send failed: {e}")
        return False


def _send_sms_message(phone_number, message):
    try:
        from django.conf import settings
        import africastalking
        africastalking.initialize(
            settings.AFRICASTALKING_USERNAME,
            settings.AFRICASTALKING_API_KEY,
        )
        sms        = africastalking.SMS
        response   = sms.send(message, [phone_number], sender_id="SKBRAND")
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        return any(r.get("status") == "Success" for r in recipients)
    except Exception as e:
        print(f"[SMS] Send failed: {e}")
        return False


# ── THANK YOU PAGE ──────────────────────────────────────────────────────────────
# ── THANK YOU PAGE ──────────────────────────────────────────────────────────────

def thank_you_view(request):
    contact_id   = request.session.get("contact_id")
    contact_name = request.session.get("contact_name", "")
    contact      = None
    whatsapp_sent = False
    sms_sent      = False
    registration_number = None  # Add this for the actual position

    if contact_id:
        try:
            contact = Contact.objects.get(pk=contact_id)
            
            # Calculate the actual registration position (based on date_added)
            registration_number = Contact.objects.filter(
                date_added__lte=contact.date_added
            ).count()
            
        except Contact.DoesNotExist:
            pass

        # Clear session immediately — prevents re-sending on refresh
        request.session.pop("contact_id", None)
        request.session.pop("contact_name", None)

    if contact and contact.full_whatsapp:
        phone  = contact.full_whatsapp.strip()
        digits = phone.replace("+", "").replace(" ", "")

        if phone.startswith("+") and digits.isdigit() and len(digits) >= 7:
            # Use registration_number instead of contact.pk in the message
            wa_message = (
                f"Hi {contact.first_name}! 👋\n\n"
                f"Welcome to the SK Brand network! 🎉\n"
                f"Your registration number is #{registration_number}.\n\n"
                f"Save this number as *S.K. Brand Links* on WhatsApp to stay connected "
                f"and receive future updates, campaigns, and opportunities.\n\n"
                f"— The SK Brand Team"
            )
            whatsapp_sent = _send_whatsapp_message(phone, wa_message)

            sms_message = (
                f"Hi {contact.first_name}, welcome to SK Brand! "
                f"Your registration number is #{registration_number}. "
                f"Save S.K. Brand Links on WhatsApp for updates. - SK Brand Team"
            )
            sms_sent = _send_sms_message(phone, sms_message)
        else:
            print(f"❌ Invalid phone number skipped: {phone}")

    return render(request, "contacts/thank_you.html", {
        "contact":       contact,
        "contact_name":  contact_name,
        "whatsapp_sent": whatsapp_sent,
        "sms_sent":      sms_sent,
        "registration_number": registration_number,  # Pass to template
    })


# ── GOOGLE OAUTH HELPERS ────────────────────────────────────────────────────────

def _get_google_flow():
    try:
        from django.conf import settings
        import google_auth_oauthlib.flow
        return google_auth_oauthlib.flow.Flow.from_client_config(
            client_config={
                "web": {
                    "client_id":     settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                    "token_uri":     "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "https://www.googleapis.com/auth/contacts",
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
            redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
        )
    except Exception as e:
        print(f"[Google OAuth] Flow build failed: {e}")
        return None


def _get_google_context():
    try:
        from .models import GoogleToken
        token = GoogleToken.objects.filter(pk=1).first()
        if token:
            return {
                "google_connected":     True,
                "google_account_email": token.email,
                "last_google_sync":     token.updated_at.strftime("%d %b %Y %H:%M"),
            }
    except Exception:
        pass
    return {
        "google_connected":     False,
        "google_account_email": "",
        "last_google_sync":     None,
    }


def _get_google_credentials():
    """Returns valid credentials, auto-refreshing if expired."""
    try:
        from django.conf import settings
        from .models import GoogleToken
        import google.oauth2.credentials
        import google.auth.transport.requests

        token = GoogleToken.objects.filter(pk=1).first()
        if not token:
            return None

        creds = google.oauth2.credentials.Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
            token.access_token = creds.token
            token.save(update_fields=["access_token", "updated_at"])

        return creds
    except Exception as e:
        print(f"[Google] Credentials error: {e}")
        return None


def _contact_to_person(contact):
    names  = contact.full_name.split(" ", 1)
    given  = names[0]
    family = names[1] if len(names) > 1 else ""
    person = {
        "names":        [{"givenName": given, "familyName": family}],
        "phoneNumbers": [{"value": contact.full_whatsapp, "type": "mobile"}],
    }
    if contact.email:
        person["emailAddresses"] = [{"value": contact.email}]
    notes = [f"Platform: {contact.platform}"]
    if contact.handle_clean: notes.append(f"Handle: @{contact.handle_clean}")
    if contact.category:     notes.append(f"Category: {contact.category}")
    if contact.country:      notes.append(f"Country: {contact.country}")
    notes.append(f"SK ID: #{contact.pk}")
    person["biographies"] = [{"value": " | ".join(notes), "contentType": "TEXT_PLAIN"}]
    return person


# ── GOOGLE OAUTH VIEWS ──────────────────────────────────────────────────────────

@login_required(login_url="login")
def google_oauth_start(request):
    from django.conf import settings

    if settings.DEBUG:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    else:
        os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)

    flow = _get_google_flow()
    if not flow:
        messages.error(
            request,
            "Google OAuth is not configured. Add GOOGLE_OAUTH_CLIENT_ID, "
            "GOOGLE_OAUTH_CLIENT_SECRET and GOOGLE_OAUTH_REDIRECT_URI to your settings.",
        )
        return redirect("sk-dashboard")

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["google_oauth_state"] = state
    return redirect(authorization_url)


@login_required(login_url="login")
def google_oauth_callback(request):
    from django.conf import settings

    if settings.DEBUG:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    else:
        os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)

    session_state  = request.session.get("google_oauth_state", "")
    callback_state = request.GET.get("state", "")
    if not session_state or session_state != callback_state:
        messages.error(
            request,
            "OAuth state mismatch — possible CSRF. Please try connecting again.",
        )
        return redirect("sk-dashboard")

    flow = _get_google_flow()
    if not flow:
        messages.error(request, "Google OAuth is not configured.")
        return redirect("sk-dashboard")

    flow.state = session_state

    try:
        auth_response = request.build_absolute_uri()
        if not settings.DEBUG:
            auth_response = auth_response.replace("http://", "https://")
        flow.fetch_token(authorization_response=auth_response)
    except Exception as e:
        messages.error(request, f"Google OAuth failed: {e}")
        return redirect("sk-dashboard")

    creds = flow.credentials

    try:
        import googleapiclient.discovery
        svc      = googleapiclient.discovery.build("oauth2", "v2", credentials=creds)
        userinfo = svc.userinfo().get().execute()
        email    = userinfo.get("email", "")
    except Exception:
        email = ""

    # ── FIX: make token_expiry timezone-aware before saving ──
    expiry = creds.expiry
    if expiry is not None and expiry.tzinfo is None:
        expiry = timezone.make_aware(expiry)

    try:
        from .models import GoogleToken
        GoogleToken.objects.update_or_create(
            pk=1,
            defaults={
                "email":         email,
                "access_token":  creds.token,
                "refresh_token": creds.refresh_token or "",
                "token_expiry":  expiry,
            },
        )
        messages.success(request, f"Google account connected: {email}")
    except Exception as e:
        messages.error(request, f"Could not save Google token: {e}")

    return redirect("sk-dashboard")


@login_required(login_url="login")
def google_disconnect(request):
    try:
        from .models import GoogleToken
        GoogleToken.objects.filter(pk=1).delete()
    except Exception:
        pass
    messages.success(request, "Google account disconnected.")
    return redirect("sk-dashboard")


@login_required(login_url="login")
def google_sync(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    creds = _get_google_credentials()
    if not creds:
        return JsonResponse(
            {"success": False, "error": "Not connected to Google. Please connect first."},
            status=401,
        )

    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    cat      = request.GET.get("category",  "").strip()
    country  = request.GET.get("country",   "").strip()
    platform = request.GET.get("platform",  "").strip()
    dfrom    = request.GET.get("date_from", "").strip()
    dto      = request.GET.get("date_to",   "").strip()
    if cat:      qs = qs.filter(category__name__iexact=cat)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    if dfrom:
        try:    qs = qs.filter(date_added__date__gte=dt.strptime(dfrom, "%Y-%m-%d").date())
        except ValueError: pass
    if dto:
        try:    qs = qs.filter(date_added__date__lte=dt.strptime(dto, "%Y-%m-%d").date())
        except ValueError: pass

    try:
        import googleapiclient.discovery
        service = googleapiclient.discovery.build("people", "v1", credentials=creds)
    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Google API init failed: {e}"},
            status=500,
        )

    synced = 0
    errors = []
    for contact in qs:
        try:
            service.people().createContact(body=_contact_to_person(contact)).execute()
            synced += 1
        except Exception as e:
            errors.append(f"#{contact.pk} {contact.full_name}: {e}")

    try:
        from .models import GoogleToken
        GoogleToken.objects.filter(pk=1).update(updated_at=timezone.now())
    except Exception:
        pass

    return JsonResponse({
        "success":      True,
        "synced_count": synced,
        "total":        qs.count(),
        "errors":       errors[:10],
    })


# ── SK ADMIN DASHBOARD ──────────────────────────────────────────────────────────

@login_required(login_url="login")
def sk_dashboard_view(request):
    now   = timezone.now()
    today = now.date()
    days  = int(request.GET.get("days", 14))
    since = today - timedelta(days=days - 1)

    total_contacts = Contact.objects.count()
    today_contacts = Contact.objects.filter(date_added__date=today).count()

    by_source_raw = list(
        Contact.objects
        .values("referral_source__label", "referral_slug")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    referral_stats = [
        {
            "label": (row.get("referral_source__label") or row.get("referral_slug") or "Direct / Unknown"),
            "count": row["count"],
        }
        for row in by_source_raw
    ]

    platform_stats = list(
        Contact.objects
        .values("platform")
        .exclude(platform="").exclude(platform__isnull=True)
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    referral_conversion_stats = []
    total_clicks = 0
    for src in ReferralSource.objects.annotate(reg_count=Count("contact")):
        clicks        = getattr(src, "click_count", 0) or 0
        registrations = src.reg_count
        total_clicks += clicks
        rate = round((registrations / clicks * 100), 1) if clicks > 0 else 0
        referral_conversion_stats.append({
            "label":           src.label,
            "clicks":          clicks,
            "registrations":   registrations,
            "conversion_rate": rate,
        })

    direct_regs = Contact.objects.filter(referral_source__isnull=True).count()
    if direct_regs:
        referral_conversion_stats.append({
            "label":           "Direct / Unknown",
            "clicks":          "—",
            "registrations":   direct_regs,
            "conversion_rate": 0,
        })

    overall_conversion_rate = (
        round(total_contacts / total_clicks * 100, 1) if total_clicks > 0 else 0
    )

    daily_qs = list(
        Contact.objects
        .filter(date_added__date__gte=since)
        .extra(select={"day": "date(date_added)"})
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    daily_map = {str(r["day"]): r["count"] for r in daily_qs}
    daily_registrations = [
        {
            "day":   since + timedelta(days=i),
            "count": daily_map.get(str(since + timedelta(days=i)), 0),
        }
        for i in range(days)
    ]

    contacts     = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    categories   = list(Category.objects.annotate(contact_count=Count("contact")).order_by("name"))
    country_list = list(
        Contact.objects.values_list("country", flat=True)
        .exclude(country="").exclude(country__isnull=True)
        .distinct().order_by("country")
    )
    category_stats = list(
        Contact.objects.values("category__name").annotate(count=Count("id")).order_by("-count")
    )

    context = {
        "total_contacts":            total_contacts,
        "today_contacts":            today_contacts,
        "days":                      days,
        "total_clicks":              total_clicks,
        "overall_conversion_rate":   overall_conversion_rate,
        "referral_stats":            referral_stats,
        "referral_conversion_stats": referral_conversion_stats,
        "platform_stats":            platform_stats,
        "platform_conversion_stats": platform_stats,
        "daily_registrations":       daily_registrations,
        "category_stats":            category_stats,
        "contacts":                  contacts,
        "categories":                categories,
        "country_list":              country_list,
    }
    context.update(_get_google_context())
    return render(request, "contacts/sk_dashboard.html", context)


# ── ORIGINAL DASHBOARD ──────────────────────────────────────────────────────────

@login_required(login_url="login")
def dashboard_view(request):
    now   = timezone.now()
    today = now.date()
    total_contacts      = Contact.objects.count()
    today_contacts      = Contact.objects.filter(date_added__date=today).count()
    this_week_contacts  = Contact.objects.filter(date_added__gte=now - timedelta(days=7)).count()
    this_month_contacts = Contact.objects.filter(date_added__gte=now - timedelta(days=30)).count()
    first            = Contact.objects.order_by("date_added").first()
    days_since_start = (today - first.date_added.date()).days if first else 0
    return render(request, "contacts/dashboard.html", {
        "total_contacts":      total_contacts,
        "today_contacts":      today_contacts,
        "this_week_contacts":  this_week_contacts,
        "this_month_contacts": this_month_contacts,
        "days_since_start":    days_since_start,
        "category_stats":      list(Contact.objects.values("category__name").annotate(count=Count("id")).order_by("-count")),
        "country_stats":       list(Contact.objects.values("country").annotate(count=Count("id")).order_by("-count")[:10]),
        "platform_stats":      list(Contact.objects.values("platform").annotate(count=Count("id")).order_by("-count")),
        "follower_stats":      list(Contact.objects.values("follower_range").annotate(count=Count("id")).order_by("-count")),
        "referral_stats":      list(Contact.objects.values("referral_source__label", "referral_slug").annotate(count=Count("id")).order_by("-count")),
        "daily_registrations": list(Contact.objects.filter(date_added__gte=now - timedelta(days=30)).extra(select={"day": "date(date_added)"}).values("day").annotate(count=Count("id")).order_by("day")),
        "recent_contacts":     Contact.objects.select_related("category").order_by("-date_added")[:10],
    })


# ── CONTACT LIST ────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def contact_list_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) | Q(surname__icontains=search) |
            Q(email__icontains=search)      | Q(whatsapp_number__icontains=search) |
            Q(handle__icontains=search)     | Q(country__icontains=search) |
            Q(region__icontains=search)
        )
    category_id    = request.GET.get("category",       "").strip()
    country        = request.GET.get("country",        "").strip()
    platform       = request.GET.get("platform",       "").strip()
    follower_range = request.GET.get("follower_range", "").strip()
    date_from      = request.GET.get("date_from",      "").strip()
    date_to        = request.GET.get("date_to",        "").strip()
    if category_id:    qs = qs.filter(category_id=category_id)
    if country:        qs = qs.filter(country__icontains=country)
    if platform:       qs = qs.filter(platform=platform)
    if follower_range: qs = qs.filter(follower_range=follower_range)
    if date_from:
        try:    qs = qs.filter(date_added__date__gte=dt.strptime(date_from, "%Y-%m-%d").date())
        except ValueError: pass
    if date_to:
        try:    qs = qs.filter(date_added__date__lte=dt.strptime(date_to, "%Y-%m-%d").date())
        except ValueError: pass

    sort = request.GET.get("sort", "-date_added")
    if sort in ["-date_added", "date_added", "first_name", "-first_name", "country", "-country"]:
        qs = qs.order_by(sort)

    return render(request, "contacts/contact_list.html", {
        "contacts":         qs,
        "total":            qs.count(),
        "total_contacts":   qs.count(),
        "today_contacts":   Contact.objects.filter(date_added__date=date.today()).count(),
        "categories":       Category.objects.filter(is_active=True),
        "country_list":     list(Contact.objects.values_list("country", flat=True).exclude(country="").distinct().order_by("country")),
        "platform_stats":   list(Contact.objects.values("platform").exclude(platform="").annotate(count=Count("id")).order_by("-count")),
        "follower_choices": Contact.FOLLOWER_RANGE_CHOICES,
        "current_filters":  {
            "search":         search,
            "category":       category_id,
            "country":        country,
            "platform":       platform,
            "follower_range": follower_range,
            "date_from":      date_from,
            "date_to":        date_to,
            "sort":           sort,
        },
    })


# ── CONTACT DETAIL API ──────────────────────────────────────────────────────────

@login_required(login_url="login")
def contact_detail_api(request, pk):
    c = get_object_or_404(Contact, pk=pk)
    return JsonResponse({
        "id":              c.id,
        "full_name":       c.full_name,
        "first_name":      c.first_name,
        "surname":         c.surname,
        "email":           c.email,
        "whatsapp":        c.full_whatsapp,
        "whatsapp_url":    c.whatsapp_chat_url,
        "country_code":    c.country_code,
        "country":         c.country,
        "region":          c.region,
        "age_range":       c.age_range,
        "category":        str(c.category) if c.category else "",
        "platform":        c.platform,
        "handle":          c.handle_clean,
        "profile_url":     c.platform_profile_url or "",
        "follower_range":  c.get_follower_range_display() if c.follower_range else "",
        "school_category": c.get_school_category_display() if c.school_category else "",
        "school_name":     c.school_name,
        "level_year":      c.level_year,
        "referral_source": str(c.referral_source) if c.referral_source else "",
        "date_added":      c.date_added.strftime("%Y-%m-%d %H:%M"),
        "days_since_added": c.days_since_added,
    })


# ── CONTACT ADD / EDIT / DELETE ─────────────────────────────────────────────────

@login_required(login_url="login")
def contact_add_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact added successfully!")
            return redirect("contact-list")
    else:
        form = ContactForm()
    return render(request, "contacts/contact_form.html", {"form": form, "title": "Add Contact"})


@login_required(login_url="login")
def contact_edit_view(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact updated successfully!")
            return redirect("contact-list")
    else:
        form = ContactForm(instance=contact)
    return render(request, "contacts/contact_form.html", {"form": form, "title": "Edit Contact"})


# ── FIX: contact_delete_view now redirects to sk-dashboard ──────────────────────
@login_required(login_url="login")
def contact_delete_view(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == "POST":
        name = contact.full_name  # capture name before deletion
        contact.delete()
        messages.success(request, f'"{name}" has been deleted.')
        return redirect("sk-dashboard")  # ← back to dashboard, not contact-list
    # GET request: show confirmation page (fallback, rarely hit from dashboard)
    return render(request, "contacts/contact_confirm_delete.html", {"contact": contact})


# ── CATEGORY VIEWS ────────────────────────────────────────────────────────────────

@login_required(login_url="login")
@require_POST
def category_toggle_view(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    cat.is_active = not cat.is_active
    cat.save(update_fields=["is_active"])
    messages.success(
        request,
        f'"{cat.name}" {"enabled" if cat.is_active else "disabled"} on registration form.',
    )
    return redirect("sk-dashboard")


@login_required(login_url="login")
@require_POST
def category_delete_view(request, pk):
    cat  = get_object_or_404(Category, pk=pk)
    name = cat.name
    cat.delete()
    messages.success(request, f'"{name}" removed. Contact data preserved.')
    return redirect("sk-dashboard")


@login_required(login_url="login")
@require_POST
def category_add_view(request):
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Category name is required.")
        return redirect("sk-dashboard")
    Category.objects.get_or_create(name=name, defaults={"is_active": True})
    messages.success(request, f'Category "{name}" added.')
    return redirect("sk-dashboard")


# ── EXPORT CSV ──────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def export_csv_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    cat      = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    dfrom    = request.GET.get("date_from", "").strip()
    dto      = request.GET.get("date_to",   "").strip()
    if cat:      qs = qs.filter(category__name__iexact=cat)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    if dfrom:
        try:    qs = qs.filter(date_added__date__gte=dt.strptime(dfrom, "%Y-%m-%d").date())
        except ValueError: pass
    if dto:
        try:    qs = qs.filter(date_added__date__lte=dt.strptime(dto, "%Y-%m-%d").date())
        except ValueError: pass

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sk_contacts_{date.today():%Y%m%d}.csv"'
    writer = csv_mod.writer(response)
    writer.writerow([
        "ID", "First Name", "Surname", "Email",
        "WhatsApp (full)", "Dial Code", "Country", "Region",
        "Age Range", "Platform", "Handle", "Follower Range",
        "Category", "School Category", "School Name", "Level/Year",
        "Referral Source", "Referral Slug", "Date Registered",
    ])
    for c in qs:
        writer.writerow([
            c.pk, c.first_name, c.surname, c.email,
            c.full_whatsapp, c.country_code, c.country, c.region, c.age_range,
            c.platform, c.handle_clean,
            c.get_follower_range_display() if c.follower_range else "",
            str(c.category) if c.category else "",
            c.get_school_category_display() if c.school_category else "",
            c.school_name,
            c.level_year if c.level_year is not None else "",
            str(c.referral_source) if c.referral_source else "",
            c.referral_slug,
            c.date_added.strftime("%Y-%m-%d %H:%M"),
        ])
    return response


# ── EXPORT VCF ──────────────────────────────────────────────────────────────────

@login_required(login_url="login")
def export_vcf_view(request):
    qs = Contact.objects.select_related("category", "referral_source").order_by("-date_added")
    cat      = request.GET.get("category", "").strip()
    country  = request.GET.get("country",  "").strip()
    platform = request.GET.get("platform", "").strip()
    dfrom    = request.GET.get("date_from", "").strip()
    dto      = request.GET.get("date_to",   "").strip()
    if cat:      qs = qs.filter(category__name__iexact=cat)
    if country:  qs = qs.filter(country__iexact=country)
    if platform: qs = qs.filter(platform__iexact=platform)
    if dfrom:
        try:    qs = qs.filter(date_added__date__gte=dt.strptime(dfrom, "%Y-%m-%d").date())
        except ValueError: pass
    if dto:
        try:    qs = qs.filter(date_added__date__lte=dt.strptime(dto, "%Y-%m-%d").date())
        except ValueError: pass

    lines = []
    for c in qs:
        parts = [f"Platform: {c.platform}"]
        if c.handle_clean:   parts.append(f"Handle: @{c.handle_clean}")
        if c.follower_range: parts.append(f"Followers: {c.get_follower_range_display()}")
        if c.category:       parts.append(f"Category: {c.category}")
        parts.append(f"Country: {c.country}")
        parts.append(f"SK ID: #{c.pk}")
        lines += [
            "BEGIN:VCARD", "VERSION:3.0",
            f"N:{c.surname};{c.first_name};;;",
            f"FN:{c.first_name} {c.surname}",
            f"TEL;TYPE=CELL:{c.full_whatsapp}",
            f"EMAIL:{c.email}",
            f"NOTE:{' | '.join(parts)}",
            "END:VCARD", "",
        ]

    response = HttpResponse("\n".join(lines), content_type="text/vcard; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="sk_contacts_{date.today():%Y%m%d}.vcf"'
    return response