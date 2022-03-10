# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0005_auto_20150504_0812'),
    ]

    operations = [
        migrations.AddField(
            model_name='categorytype',
            name='vendor_editable',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
