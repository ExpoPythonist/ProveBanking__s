# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
import djorm_pgarray.fields
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20150402_0605'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='organization_name',
            field=models.CharField(max_length=124, verbose_name='organization', blank=True),
            preserve_default=True,
        ),
    ]
