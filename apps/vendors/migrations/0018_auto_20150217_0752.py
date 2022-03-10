# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0017_auto_20150211_1612'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='kynd',
            field=models.PositiveSmallIntegerField(default=2, choices=[(1, b'preferred'), (2, b'approved'), (3, b'prospective')]),
            preserve_default=True,
        ),
    ]
