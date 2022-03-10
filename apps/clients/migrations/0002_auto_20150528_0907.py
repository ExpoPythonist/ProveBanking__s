# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='logo',
            field=sorl.thumbnail.fields.ImageField(upload_to=b'images/logo/', null=True, verbose_name='Client logo', blank=True),
            preserve_default=True,
        ),
    ]
