from pywebpush import webpush, WebPushException
from django.conf import settings
import json
from .models import WebPushSubscription


def send_web_push_notification(title, body,url):
    subscriptions = WebPushSubscription.objects.all()
    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subscriptions:
        try:
            response = webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS
            )
            print(f"Notificación enviada con éxito a {sub.endpoint}. Respuesta: {response}")
        except WebPushException as ex:
            print(f"Error enviando push a {sub.endpoint}: {ex}")
