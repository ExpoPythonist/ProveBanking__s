# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0004_auto_20141124_0732'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendortype',
            name='slug',
            field=models.TextField(unique=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
