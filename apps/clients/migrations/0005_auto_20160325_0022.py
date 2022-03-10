# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_auto_20160324_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='annual_revenue',
            field=models.BigIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='client',
            name='market_cap',
            field=models.BigIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
