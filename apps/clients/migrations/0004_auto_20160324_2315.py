# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_auto_20160324_1744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='client_quality_score',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=4, blank=True, null=True, verbose_name=b'Client Quality Score'),
            preserve_default=True,
        ),
    ]
