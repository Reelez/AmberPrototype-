import hashlib

from django.db import migrations, models


def dedupe_and_hash_endpoints(apps, schema_editor):
    """Keep the newest row per endpoint and fill endpoint_hash before it becomes unique."""
    Subscription = apps.get_model('notificaciones', 'WebPushSubscription')
    seen = set()
    for sub in Subscription.objects.order_by('-id'):
        digest = hashlib.sha256(sub.endpoint.encode('utf-8')).hexdigest()
        if digest in seen:
            sub.delete()
            continue
        seen.add(digest)
        sub.endpoint_hash = digest
        sub.save(update_fields=['endpoint_hash'])


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0002_alter_webpushsubscription_endpoint'),
    ]

    operations = [
        migrations.AddField(
            model_name='webpushsubscription',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='webpushsubscription',
            name='endpoint_hash',
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(dedupe_and_hash_endpoints, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='webpushsubscription',
            name='endpoint_hash',
            field=models.CharField(editable=False, max_length=64, unique=True),
        ),
    ]
