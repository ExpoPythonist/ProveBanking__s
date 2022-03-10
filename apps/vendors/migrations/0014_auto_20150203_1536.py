# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0013_auto_20150203_0558'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='engage_step',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
