# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='kind',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'category'), (2, b'industry'), (1, b'skill'), (3, b'language')]),
        ),
    ]
