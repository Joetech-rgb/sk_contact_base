import hashlib
import functools
from django.http import JsonResponse
from .models import APIKey


def require_api_key(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        raw_key = request.headers.get("X-Api-Key", "").strip()
        if not raw_key:
            return JsonResponse({"error": "Authentication required. Pass X-Api-Key header."}, status=401)
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        try:
            api_key = APIKey.objects.get(key_hash=hashed, is_active=True)
        except APIKey.DoesNotExist:
            return JsonResponse({"error": "Invalid or inactive API key."}, status=403)
        api_key.record_use()
        request.api_key = api_key
        return view_func(request, *args, **kwargs)
    return wrapper
