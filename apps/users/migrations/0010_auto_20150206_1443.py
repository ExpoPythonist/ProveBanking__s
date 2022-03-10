# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('divisions', '0002_division_slug'),
        ('users', '0009_auto_20150206_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='divisions',
            field=models.ManyToManyField(related_name='users', through='users.UserDivisionRel', to='divisions.Division'),
            preserve_default=True,
        ),
    ]
