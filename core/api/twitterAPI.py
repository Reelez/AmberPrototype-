import requests
import os
from django.conf import settings

# Credenciales de Twitter desde settings.py
API_KEY = settings.TWITTER_API_KEY
API_SECRET = settings.TWITTER_API_SECRET
ACCESS_TOKEN = settings.TWITTER_ACCESS_TOKEN
ACCESS_TOKEN_SECRET = settings.TWITTER_ACCESS_TOKEN_SECRET
BEARER_TOKEN = settings.TWITTER_BEARER_TOKEN

# Endpoint de publicación de tweets
TWEET_URL = "https://api.twitter.com/2/tweets"

# Autenticación OAuth 1.0a
from requests_oauthlib import OAuth1

auth = OAuth1(
    API_KEY,
    API_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)

def publicar_tweet(texto, imagen_path=None):
    """
    Publica un tweet en la cuenta conectada.
    :param texto: Texto del tweet.
    :param imagen_path: Ruta de la imagen a subir (opcional).
    :return: True si éxito, False si error.
    """
    try:
        if imagen_path:
            media_id = subir_imagen(imagen_path)
            if not media_id:
                print("❌ Error al subir la imagen a Twitter.")
                return False
        else:
            media_id = None

        payload = {
            "text": texto
        }

        if media_id:
            # API v2 no admite media_id directamente, así que se usaría v1.1 aquí si es necesario
            return publicar_tweet_v1(texto, media_id)

        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(TWEET_URL, json=payload, headers=headers)

        if response.status_code == 201:
            print("✅ Tweet publicado correctamente.")
            return True
        else:
            print(f"❌ Error al publicar tweet: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"⚠️ Excepción al publicar tweet: {e}")
        return False


def subir_imagen(imagen_path):
    """
    Sube una imagen a Twitter y devuelve el media_id.
    Requiere usar la API v1.1 para upload/media.
    """
    try:
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        with open(imagen_path, 'rb') as img_file:
            files = {
                'media': img_file
            }
            response = requests.post(upload_url, auth=auth, files=files)

        if response.status_code == 200:
            media_id = response.json().get("media_id_string")
            print(f"✅ Imagen subida con media_id: {media_id}")
            return media_id
        else:
            print(f"❌ Error al subir imagen: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"⚠️ Excepción al subir imagen: {e}")
        return None


def publicar_tweet_v1(texto, media_id):
    """
    Publica un tweet con imagen usando API v1.1 (solo para media).
    """
    try:
        url = "https://api.twitter.com/1.1/statuses/update.json"
        payload = {
            "status": texto,
            "media_ids": media_id
        }
        response = requests.post(url, auth=auth, data=payload)

        if response.status_code == 200:
            print("✅ Tweet con imagen publicado correctamente.")
            return True
        else:
            print(f"❌ Error al publicar tweet con imagen: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"⚠️ Excepción al publicar tweet con imagen: {e}")
        return False
