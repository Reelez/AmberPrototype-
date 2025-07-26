from twilio.rest import Client
from django.conf import settings
from core.models import UserSMS

def enviar_sms(alerta, url):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        mensaje = (
            f"🔴 Alerta AMBER: {alerta.nombre_desaparecido} desapareció en {alerta.ultima_ubicacion}. "
            f"Más info: {url} Llama al 104."
        )
        for usuario in UserSMS.objects.all():
            try:
                client.messages.create(
                    body=mensaje,
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=usuario.telefono
                )
                print(f"✅ SMS enviado a {usuario.telefono}")
            except Exception as e:
                print(f"❌ Error al enviar SMS a {usuario.telefono}: {e}")
    except Exception as e:
        print(f"❌ Error creando cliente Twilio: {e}")
