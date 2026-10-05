import json
import logging
from urllib.parse import urlparse

from django.db import DatabaseError, transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

from .models import WebPushSubscription

logger = logging.getLogger(__name__)

# Only real browser push services are accepted as endpoints. The server POSTs to every
# stored endpoint on each broadcast, so arbitrary URLs would allow SSRF against internal hosts.
ALLOWED_PUSH_HOST_SUFFIXES = (
    'fcm.googleapis.com',           # Chrome and Chromium-based browsers
    'push.services.mozilla.com',    # Firefox
    'notify.windows.com',           # Edge on Windows
    'push.apple.com',               # Safari
)


def is_allowed_push_endpoint(endpoint):
    parsed = urlparse(endpoint)
    host = (parsed.hostname or '').lower()
    return parsed.scheme == 'https' and any(
        host == suffix or host.endswith('.' + suffix) for suffix in ALLOWED_PUSH_HOST_SUFFIXES
    )


@csrf_exempt
def save_subscription(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        data = json.loads(request.body)
        endpoint = data['endpoint']
        auth = data['keys']['auth']
        p256dh = data['keys']['p256dh']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid subscription payload'}, status=400)

    if (
        not all(isinstance(v, str) and v for v in (endpoint, auth, p256dh))
        or len(endpoint) > 1000
        or len(auth) > 255
        or len(p256dh) > 255
        or not is_allowed_push_endpoint(endpoint)
    ):
        return JsonResponse({'status': 'error', 'message': 'Invalid subscription payload'}, status=400)

    # The browser may post the same subscription twice at once (button click and
    # silent refresh); retry once if both requests collide on the unique hash.
    for attempt in range(2):
        try:
            with transaction.atomic():
                _, created = WebPushSubscription.objects.update_or_create(
                    endpoint_hash=WebPushSubscription.hash_endpoint(endpoint),
                    defaults={'endpoint': endpoint, 'auth': auth, 'p256dh': p256dh},
                )
            break
        except DatabaseError:
            if attempt == 1:
                raise
            logger.warning("Subscription save collided; retrying once")
    logger.info("Subscription %s", "created" if created else "updated")
    return JsonResponse({'status': 'subscription saved', 'created': created})
