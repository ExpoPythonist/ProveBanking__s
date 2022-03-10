# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0027_auto_20150408_0858'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='is_global',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
