# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
import djorm_pgarray.fields
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_auto_20150321_1749'),
    ]

    operations = [
        migrations.RunSQL(
            'ALTER TABLE users_user'
            ' ALTER COLUMN meta'
            ' SET DATA TYPE jsonb'
            ' USING meta::jsonb;'
        ),
    ]
