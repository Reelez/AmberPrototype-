import requests
from django.conf import settings

def verificar_recaptcha(token):
    if not token:
        return False

    secret_key = settings.RECAPTCHA_SECRET_KEY
    url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': secret_key,
        'response': token
    }

    try:
        r = requests.post(url, data=data)
        result = r.json()

        # Debe ser éxito y score > 0.5 (ajusta según tu necesidad)
        if result.get('success') and result.get('score', 0) >= 0.5:
            return True
        else:
            print('reCAPTCHA fallo:', result)
            return False

    except Exception as e:
        print('Error validando reCAPTCHA:', e)
        return False
