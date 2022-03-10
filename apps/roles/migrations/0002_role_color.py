# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='color',
            field=colorfield.fields.ColorField(default=b'#FFFFFF', max_length=10),
            preserve_default=True,
        ),
    ]
