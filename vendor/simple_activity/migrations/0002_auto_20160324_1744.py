# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simple_activity', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='actor',
        ),
        migrations.RemoveField(
            model_name='action',
            name='item_type',
        ),
        migrations.RemoveField(
            model_name='action',
            name='target_type',
        ),
        migrations.DeleteModel(
            name='Action',
        ),
    ]
