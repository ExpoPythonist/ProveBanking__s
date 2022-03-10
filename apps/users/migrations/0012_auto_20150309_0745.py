# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_auto_20150209_0739'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_dedicated',
        ),
    ]
