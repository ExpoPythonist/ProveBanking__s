# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0020_auto_20150217_1613'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vendor',
            old_name='kynd',
            new_name='kind'
        )
    ]
