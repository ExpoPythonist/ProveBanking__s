# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import vendors.models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0028_auto_20150424_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='search_keywords',
            field=djorm_pgarray.fields.TextArrayField(default=vendors.models.default_array, dbtype='text'),
            preserve_default=True,
        ),
    ]
