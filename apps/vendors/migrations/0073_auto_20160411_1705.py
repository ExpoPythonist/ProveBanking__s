# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0072_auto_20160406_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientreference',
            name='duration',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, 'less than 1 year'), (2, '1 - 3 years'), (3, '3 - 5 years'), (4, '5 - 10 years'), (5, '10+ years')]),
            preserve_default=True,
        ),
    ]
