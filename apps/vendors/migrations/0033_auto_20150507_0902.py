# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0032_auto_20150507_0902'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='portfolioitem',
            name='location',
        ),
        migrations.AlterField(
            model_name='portfolioitem',
            name='locations',
            field=models.ManyToManyField(related_name='portfolio', null=True, to='locations.Location', blank=True),
            preserve_default=True,
        ),
    ]
