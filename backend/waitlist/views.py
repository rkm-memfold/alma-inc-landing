import json

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import WaitlistEntry


def _client_ip(request):
    # nginx sets X-Real-IP; REMOTE_ADDR is the loopback proxy otherwise.
    return request.headers.get("X-Real-IP") or request.META.get("REMOTE_ADDR")


def healthz(request):
    return JsonResponse({"ok": True})


# The landing page is static HTML with no CSRF token to embed. The endpoint is
# same-origin only in practice (nginx vhost), idempotent, and rate-limited at
# nginx, so CSRF protection is deliberately skipped here.
@csrf_exempt
@require_POST
def join_waitlist(request):
    if request.content_type == "application/json":
        try:
            email = (json.loads(request.body or b"{}").get("email") or "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)
    else:
        email = (request.POST.get("email") or "").strip()

    email = email.lower()
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "invalid email"}, status=400)

    _, created = WaitlistEntry.objects.get_or_create(
        email=email,
        defaults={
            "ip_address": _client_ip(request),
            "user_agent": request.headers.get("User-Agent", "")[:512],
        },
    )
    return JsonResponse({"ok": True, "created": created})
