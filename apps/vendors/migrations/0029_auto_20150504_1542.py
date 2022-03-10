# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0028_auto_20150424_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='procurementcontact',
            name='always_show',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
