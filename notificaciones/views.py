from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseNotAllowed
import json
from .models import WebPushSubscription

@csrf_exempt
def save_subscription(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos para suscripción:", data)
            WebPushSubscription.objects.create(
                endpoint=data['endpoint'],
                auth=data['keys']['auth'],
                p256dh=data['keys']['p256dh']
            )
            return JsonResponse({'status': 'subscription saved'})
        except Exception as e:
            print("Error guardando suscripción:", e)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])
