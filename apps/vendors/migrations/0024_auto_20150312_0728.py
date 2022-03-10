# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0023_auto_20150225_0834'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='engage_link',
        ),
        migrations.AddField(
            model_name='vendor',
            name='engage_process',
            field=models.TextField(max_length=500, null=True, blank=True),
            preserve_default=True,
        ),
    ]

