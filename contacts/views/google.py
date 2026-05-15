# contacts/views/google.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from ..models import GoogleToken


def _get_flow():
    from google_auth_oauthlib.flow import Flow
    from django.conf import settings
    flow = Flow.from_client_config(
        {"web": {
            "client_id":     settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
        }},
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ],
    )
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    return flow


@login_required(login_url="login")
def google_oauth_start(request):
    flow = _get_flow()
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    request.session["google_oauth_state"] = state
    return redirect(auth_url)


@login_required(login_url="login")
def google_oauth_callback(request):
    state = request.session.get("google_oauth_state")
    flow  = _get_flow()
    flow.fetch_token(authorization_response=request.build_absolute_uri(), state=state)
    credentials = flow.credentials
    from googleapiclient.discovery import build as g_build
    service   = g_build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()
    email     = user_info.get("email", "unknown@google.com")
    token, _  = GoogleToken.objects.update_or_create(
        email=email,
        defaults={"access_token": credentials.token, "refresh_token": credentials.refresh_token or ""},
    )
    token.set_expiry(credentials.expiry)
    token.save()
    messages.success(request, f"Google account connected: {email}")
    return redirect("dashboard")


@login_required(login_url="login")
def google_disconnect(request):
    if request.method == "POST":
        GoogleToken.objects.all().delete()
        messages.success(request, "Google account disconnected.")
    return redirect("dashboard")


@login_required(login_url="login")
def google_sync(request):
    if request.method != "POST":
        return redirect("dashboard")
    try:
        from ..services.google_drive import upload_contacts_backup
        result = upload_contacts_backup()
        messages.success(request, f"Sync complete: {result}")
    except Exception as exc:
        messages.error(request, f"Sync failed: {exc}")
    return redirect("dashboard")
