# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0019_auto_20150217_1611'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='kind',
        ),
    ]
