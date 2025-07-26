from django.db import models

class WebPushSubscription(models.Model):
    endpoint = models.URLField(max_length=1000)  # Aumentado para evitar errores
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)
