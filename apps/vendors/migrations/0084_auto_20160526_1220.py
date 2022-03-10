# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-26 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0083_auto_20160515_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='website',
            field=models.URLField(blank=True, default='', max_length=255, verbose_name='Website'),
        ),
    ]