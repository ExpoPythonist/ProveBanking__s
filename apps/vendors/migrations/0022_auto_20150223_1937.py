# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0021_auto_20150217_1655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='engage_step',
        ),
        migrations.AddField(
            model_name='vendor',
            name='engage_link',
            field=models.URLField(default=b'', max_length=127, verbose_name='engage_link', blank=True),
            preserve_default=True,
        ),
    ]
