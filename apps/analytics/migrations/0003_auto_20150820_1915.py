# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_pageview_views'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageview',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 8, 20, 19, 15, 32, 679060, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
