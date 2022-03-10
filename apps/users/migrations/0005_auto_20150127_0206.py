# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20141223_0836'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_staffable',
            field=models.BooleanField(default=True, verbose_name=b'Can be staffed'),
            preserve_default=True,
        ),
    ]
