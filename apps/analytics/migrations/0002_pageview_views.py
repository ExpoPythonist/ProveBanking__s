# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import analytics.models
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageview',
            name='views',
            field=djorm_pgarray.fields.DateTimeArrayField(default=analytics.models._default_views, dbtype='timestamp with time zone'),
            preserve_default=True,
        ),
    ]
