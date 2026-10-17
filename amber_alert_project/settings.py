from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',') if h.strip()]
railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_domain and railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(railway_domain)
if '.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.railway.app')

# Needed when the app is reached through an HTTPS tunnel or domain (e.g. https://xyz.trycloudflare.com or railway)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if o.strip()]
if railway_domain:
    railway_url = f"https://{railway_domain}"
    if railway_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(railway_url)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'core',
    'notificaciones',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'amber_alert_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.vapid_public_key',
            ],
        },
    },
]

WSGI_APPLICATION = 'amber_alert_project.wsgi.application'

DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    db_config = dj_database_url.parse(DATABASE_URL)
    if DATABASE_URL.startswith('mysql://'):
        db_config['ENGINE'] = 'mysql.connector.django'
    DATABASES = {
        'default': db_config
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'mysql.connector.django',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='3306'),
        }
    }

VAPID_PUBLIC_KEY = config('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY')
VAPID_CLAIMS = {
    "sub": f"mailto:{config('VAPID_CLAIMS_EMAIL')}"
}

# Dispatch Web Push in a background thread (set False to run synchronously, e.g. in tests)
WEBPUSH_ASYNC = config('WEBPUSH_ASYNC', default=True, cast=bool)

# CAP v1.2 <sender> value
CAP_SENDER = config('CAP_SENDER', default='alerta-amber@amber.pa')

LOGIN_URL = 'login'

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Panama'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'std': {
            'format': '[%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'std',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'core': {'level': 'INFO'},
        'notificaciones': {'level': 'INFO'},
    },
}
