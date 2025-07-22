from django.db import models

class WebPushSubscription(models.Model):
    endpoint = models.URLField()
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)
