# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='expanded',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='kind',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'city'), (2, b'state'), (3, b'country')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='slug',
            field=autoslug.fields.AutoSlugField(null=True, editable=False, blank=True, unique=True),
        ),
    ]
