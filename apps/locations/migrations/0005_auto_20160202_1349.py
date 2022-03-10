# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0004_auto_20151218_1826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='location_id',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='parent',
            field=models.ForeignKey(related_name='children', blank=True, to='locations.Location', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='parent_idx',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
