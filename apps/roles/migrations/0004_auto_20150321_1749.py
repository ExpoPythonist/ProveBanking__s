# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0003_auto_20150121_1903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='color',
            field=colorfield.fields.ColorField(default=b'#f2f1f0', max_length=10),
            preserve_default=True,
        ),
    ]
