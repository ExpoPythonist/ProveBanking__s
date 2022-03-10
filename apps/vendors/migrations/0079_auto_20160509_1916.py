# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0078_auto_20160502_1339'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rfp',
            name='description',
            field=models.TextField(verbose_name='Please describe the job in more detail', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rfp',
            name='masked',
            field=models.BooleanField(default=False, verbose_name='Keep my number hidden'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rfp',
            name='question',
            field=models.CharField(max_length=1000, verbose_name='What do you want done?'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rfp',
            name='vendors',
            field=models.ManyToManyField(related_name='rfps', verbose_name="Companies you've chosen", to='vendors.Vendor', through='vendors.Bid', blank=True),
            preserve_default=True,
        ),
    ]
