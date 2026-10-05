import json
import logging

from django.conf import settings
from pywebpush import webpush, WebPushException

from .models import WebPushSubscription

logger = logging.getLogger(__name__)

# Push services answer with these codes when a subscription no longer exists.
EXPIRED_STATUS_CODES = (404, 410)

# How long the push service keeps an undelivered message. An AMBER alert stays
# active for 24 hours in Panama, and WNS (Edge) rejects TTL=0 with HTTP 400.
PUSH_TTL_SECONDS = 24 * 60 * 60
PUSH_HEADERS = {"Urgency": "high"}


def send_web_push_notification(title, body, url):
    """Send a Web Push message to every stored subscription.

    Subscriptions rejected by the push service with 404/410 are deleted.
    Returns a summary dict: {'sent': int, 'failed': int, 'deleted': int}.
    """
    payload = json.dumps({"title": title, "body": body, "url": url})
    summary = {"sent": 0, "failed": 0, "deleted": 0}

    for sub in WebPushSubscription.objects.all():
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=payload,
                ttl=PUSH_TTL_SECONDS,
                headers=dict(PUSH_HEADERS),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=dict(settings.VAPID_CLAIMS),
            )
            summary["sent"] += 1
        except WebPushException as ex:
            status_code = getattr(getattr(ex, "response", None), "status_code", None)
            if status_code in EXPIRED_STATUS_CODES:
                sub.delete()
                summary["deleted"] += 1
                logger.info("Deleted expired subscription %s (HTTP %s)", sub.endpoint, status_code)
            else:
                summary["failed"] += 1
                logger.warning("Push to %s failed (HTTP %s): %s", sub.endpoint, status_code, ex)
        except Exception:
            summary["failed"] += 1
            logger.exception("Unexpected error sending push to %s", sub.endpoint)

    logger.info("Web Push summary: %s", summary)
    return summary
