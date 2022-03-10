# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0029_auto_20150504_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='summary',
            field=models.CharField(default=b'',
                                   max_length=500,
                                   verbose_name='Summary'),
            preserve_default=True,
        ),
    ]
