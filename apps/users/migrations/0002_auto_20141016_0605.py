# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='pending_setup_steps',
            field=djorm_pgarray.fields.ArrayField(default='{1, 3}', verbose_name='Pending steps'),
        ),
    ]
