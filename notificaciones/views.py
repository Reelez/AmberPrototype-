from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseNotAllowed
import json
from .models import WebPushSubscription
from django.conf import settings
from decouple import config
from cryptography.fernet import Fernet

@csrf_exempt
def save_subscription(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos para suscripción:", data)

            # Cifrado
            secret_key = config('FERNET_SECRET_KEY').encode()
            f = Fernet(secret_key) 
            endpoint = data['endpoint']
            auth = f.encrypt(data['keys']['auth'].encode()).decode()
            p256dh = f.encrypt(data['keys']['p256dh'].encode()).decode()

            WebPushSubscription.objects.create(
                endpoint=endpoint,
                auth=auth,
                p256dh=p256dh
            )
            return JsonResponse({'status': 'subscription saved'})
        except Exception as e:
            print("Error guardando suscripción:", e)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])