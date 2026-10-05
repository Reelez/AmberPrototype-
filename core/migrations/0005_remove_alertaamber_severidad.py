from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_severidad_otros_detalles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alertaamber',
            name='severidad',
        ),
    ]
