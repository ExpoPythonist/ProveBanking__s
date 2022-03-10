# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('divisions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='division',
            name='slug',
            field=models.TextField(unique=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
