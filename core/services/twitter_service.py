from core.api.twitterAPI import publicar_tweet
from core.utils.image_generator import generate_alert_image

def publicar_alerta_en_twitter(alerta, descripcion):
    try:
        imagen_generada = generate_alert_image(alerta)
        publicar_tweet(descripcion, imagen_generada)
        print("✅ Alerta publicada en Twitter.")
    except Exception as e:
        print(f"❌ Error al publicar en Twitter: {e}")
