# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20150128_0409'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='next_available',
            field=models.DateField(default=datetime.date(1970, 1, 1), null=True, editable=False, blank=True),
            preserve_default=True,
        ),
    ]
