# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('divisions', '0002_division_slug'),
        ('users', '0003_auto_20141125_0305'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='divisions',
            field=models.ManyToManyField(related_name=b'users', to='divisions.Division'),
            preserve_default=True,
        ),
    ]
