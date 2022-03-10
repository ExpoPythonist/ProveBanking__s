# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0075_auto_20160421_0404'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='insuranceverification',
            name='remind_me',
        ),
        migrations.AlterField(
            model_name='insuranceverification',
            name='expiry_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='insuranceverification',
            name='extent',
            field=models.IntegerField(null=True, choices=[(1, '\u20ac2.6 million'), (2, '\u20ac6.5 million'), (3, 'Other (please specify)')]),
            preserve_default=True,
        ),
    ]
