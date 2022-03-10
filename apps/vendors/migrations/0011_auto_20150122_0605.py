# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import vendors.models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0010_auto_20150121_0936'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='glassdoor',
            field=models.URLField(default=b'', max_length=255, verbose_name='Glassdoor', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='vendor',
            name='pending_edit_steps',
            field=djorm_pgarray.fields.ArrayField(default=vendors.models.default_pending_steps, verbose_name='Pending steps'),
            preserve_default=True,
        ),
    ]
