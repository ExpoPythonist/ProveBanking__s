# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0030_auto_20150507_0829'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioitem',
            name='locations',
            field=models.ManyToManyField(related_name='portfolios', null=True, to='locations.Location', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='portfolioitem',
            name='end_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
