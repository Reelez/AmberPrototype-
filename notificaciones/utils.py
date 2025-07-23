from pywebpush import webpush, WebPushException
from django.conf import settings
import json
from .models import WebPushSubscription
from cryptography.fernet import Fernet
from decouple import config


def send_web_push_notification(title, body, url):
    secret_key = config('FERNET_SECRET_KEY').encode()
    f = Fernet(secret_key)  # Instancia local de Fernet
    subscriptions = WebPushSubscription.objects.all()
    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subscriptions:
        try:
            endpoint = f.decrypt(sub.endpoint.encode()).decode()
            p256dh = f.decrypt(sub.p256dh.encode()).decode()
            auth = f.decrypt(sub.auth.encode()).decode()

            response = webpush(
                subscription_info={
                    "endpoint": endpoint,
                    "keys": {
                        "p256dh": p256dh,
                        "auth": auth
                    }
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS
            )
            print(f"Notificación enviada con éxito a {endpoint}. Respuesta: {response}")

        except WebPushException as ex:
            print(f"Error enviando push a {sub.id}: {ex}")
        except Exception as e:
            print(f"Error descifrando datos para {sub.id}: {e}")