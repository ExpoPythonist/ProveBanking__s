# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
import djorm_pgarray.fields
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20150323_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='meta',
            field=django_pgjson.fields.JsonBField(default=users.models._default_user_meta),
            preserve_default=True,
        ),
    ]
