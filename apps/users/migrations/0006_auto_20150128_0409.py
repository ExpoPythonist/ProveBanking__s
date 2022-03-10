# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20150127_0206'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_dedicated',
            field=models.BooleanField(default=False, verbose_name=b'Can be staffed'),
            preserve_default=True,
        ),
    ]
