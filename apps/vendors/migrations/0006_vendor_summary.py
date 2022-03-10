# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0005_vendortype_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='summary',
            field=models.CharField(default=b'', max_length=140, verbose_name='Summary', blank=True),
            preserve_default=True,
        ),
    ]
