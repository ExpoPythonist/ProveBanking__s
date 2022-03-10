# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0038_auto_20150624_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorlocation',
            name='num_resources',
            field=models.PositiveIntegerField(default=1, verbose_name='Number of employees'),
            preserve_default=True,
        ),
    ]
