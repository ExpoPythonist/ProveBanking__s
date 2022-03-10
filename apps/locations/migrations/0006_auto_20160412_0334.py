# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0005_auto_20160202_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='slug',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=False,
        ),
    ]
