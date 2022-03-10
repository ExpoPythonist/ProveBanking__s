# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0024_auto_20150312_0728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='story',
            field=models.TextField(max_length=1000, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='vendor',
            name='summary',
            field=models.CharField(default=b'', max_length=140, verbose_name='Summary'),
            preserve_default=True,
        ),
    ]
