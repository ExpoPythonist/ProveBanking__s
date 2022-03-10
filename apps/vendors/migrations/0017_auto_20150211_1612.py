# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0016_auto_20150211_1438'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorkind',
            name='title',
            field=models.CharField(default=b'', max_length=127, verbose_name='Title', blank=True),
            preserve_default=True,
        ),
    ]
