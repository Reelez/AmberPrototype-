from notificaciones.utils import send_web_push_notification

def enviar_web_push(titulo, mensaje, url):
    try:
        send_web_push_notification(titulo, mensaje, url)
        print("✅ Web Push enviado correctamente.")
    except Exception as e:
        print(f"❌ Error en Web Push: {e}")
