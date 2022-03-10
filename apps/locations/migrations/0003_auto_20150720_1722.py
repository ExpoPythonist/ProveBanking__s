# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models, migrations
import csv
import os
from locations.models import Location


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0002_auto_20141207_0757'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='location_id',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='parent',
            field=models.ForeignKey(to='locations.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='parent_idx',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
