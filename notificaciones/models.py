import hashlib

from django.db import models


class WebPushSubscription(models.Model):
    endpoint = models.URLField(max_length=1000)
    # SHA-256 of the endpoint: endpoints can exceed the index size limit of MySQL,
    # so uniqueness is enforced on this fixed-length digest instead.
    endpoint_hash = models.CharField(max_length=64, unique=True, editable=False)
    auth = models.CharField(max_length=255)
    p256dh = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    @staticmethod
    def hash_endpoint(endpoint):
        return hashlib.sha256(endpoint.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        self.endpoint_hash = self.hash_endpoint(self.endpoint)
        super().save(*args, **kwargs)
