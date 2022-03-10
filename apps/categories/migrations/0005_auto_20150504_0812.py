# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0004_auto_20150317_0723'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('slug',), 'verbose_name': 'category', 'verbose_name_plural': 'categories'},
        ),
    ]
