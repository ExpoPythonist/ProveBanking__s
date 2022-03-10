# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0004_reviewtoken_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='vendor_viewable',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
